import asyncio
import json
import math
import os
import signal
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import aiohttp
except ImportError:  # Lazy hint for user
    aiohttp = None  # type: ignore


@dataclass
class Result:
    status: int
    ok: bool
    latency_ms: float
    error: Optional[str]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def percentile(values: List[float], p: float) -> float:
    if not values:
        return float("nan")
    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def build_payload(args) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "temperature": args.temperature,
        "stream": False,
    }
    if args.extra:
        try:
            extra_dict = json.loads(args.extra)
            if isinstance(extra_dict, dict):
                payload.update(extra_dict)
        except json.JSONDecodeError:
            pass
    if args.payload_file and os.path.exists(args.payload_file):
        with open(args.payload_file, "r", encoding="utf-8") as f:
            from_file = json.load(f)
            if isinstance(from_file, dict):
                payload.update(from_file)
    return payload


async def ngrok_warmup(session: "aiohttp.ClientSession", base_url: str) -> bool:
    """ngrok 預熱機制：先發送 GET 請求來喚醒服務"""
    try:
        print("🔄 ngrok 預熱中...")
        warmup_headers = {"ngrok-skip-browser-warning": "true"}
        
        async with session.get(
            base_url,
            headers=warmup_headers,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            print(f"   預熱 GET 請求狀態碼: {resp.status}")
            if resp.status == 200:
                print("   ✅ ngrok 預熱成功")
                return True
            else:
                print(f"   ⚠️  ngrok 預熱回應異常: {resp.status}")
                return False
    except Exception as e:
        print(f"   ❌ ngrok 預熱失敗: {e}")
        return False


async def rate_limiter(rps: Optional[float]):
    if rps and rps > 0:
        await asyncio.sleep(1.0 / rps)


async def worker(
    name: str,
    session: "aiohttp.ClientSession",
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    queue: "asyncio.Queue[int]",
    results: List[Result],
    timeout_s: float,
    rps: Optional[float],
    worker_id: int,
):
    """改進的 worker 函數，加入 ngrok 適應性"""
    while True:
        try:
            _ = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        
        start = time.perf_counter()
        error_msg = None
        status = 0
        ok = False
        p_tok = c_tok = t_tok = 0
        
        try:
            # 如果是第一個請求，稍微延遲以適應 ngrok
            if worker_id == 0 and len(results) == 0:
                await asyncio.sleep(0.5)
            
            print(f"📤 發送請求到: {url}")
            print(f"請求標頭: {json.dumps(dict(headers), ensure_ascii=False, indent=2)}")
            print(f"請求內容: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout_s),
            ) as resp:
                status = resp.status
                print(f"回應狀態碼: {status}")
                print(f"回應標頭: {dict(resp.headers)}")
                
                # Drain response and parse JSON for usage metrics
                text = await resp.text()
                ok = 200 <= status < 300
                
                if text:
                    try:
                        data = json.loads(text)
                        print(f"回應內容: {json.dumps(data, ensure_ascii=False, indent=2)}")
                        usage = data.get("usage") if isinstance(data, dict) else None
                        if isinstance(usage, dict):
                            p_tok = int(usage.get("prompt_tokens") or 0)
                            c_tok = int(usage.get("completion_tokens") or 0)
                            t_tok = int(usage.get("total_tokens") or (p_tok + c_tok))
                    except Exception as e:  # noqa: BLE001
                        print(f"JSON 解析錯誤: {e}")
                        print(f"原始回應: {text[:500]}...")
                        pass
                else:
                    print("回應內容為空")
                        
        except asyncio.TimeoutError:
            error_msg = "請求逾時"
            print(f"❌ 請求逾時: {timeout_s} 秒")
        except Exception as e:  # noqa: BLE001
            error_msg = str(e)
            print(f"❌ 請求錯誤: {e}")
        finally:
            end = time.perf_counter()
            latency_ms = (end - start) * 1000.0
            
            try:
                results.append(
                    Result(
                        status=status,
                        ok=ok,
                        latency_ms=latency_ms,
                        error=error_msg,
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        total_tokens=t_tok,
                    )
                )
            except Exception:
                results.append(Result(status=status, ok=ok, latency_ms=latency_ms, error=error_msg))
            
            if rps:
                await rate_limiter(rps)
            queue.task_done()


def format_number(n: float) -> str:
    if math.isnan(n):
        return "NaN"
    if n >= 1000:
        return f"{n:,.0f}"
    return f"{n:.2f}"


def print_report(results: List[Result], started_at: float, finished_at: float):
    total = len(results)
    success = sum(1 for r in results if r.ok)
    failed = total - success
    duration_s = max(1e-9, finished_at - started_at)
    rps = total / duration_s
    duration_min = duration_s / 60.0

    latencies = sorted([r.latency_ms for r in results])
    avg = statistics.fmean(latencies) if latencies else float("nan")
    p50 = percentile(latencies, 0.50)
    p90 = percentile(latencies, 0.90)
    p95 = percentile(latencies, 0.95)
    p99 = percentile(latencies, 0.99)
    p999 = percentile(latencies, 0.999)
    mx = max(latencies) if latencies else float("nan")

    status_counts: Dict[int, int] = {}
    for r in results:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1

    # LLM usage metrics
    total_prompt_tokens = sum(r.prompt_tokens for r in results)
    total_completion_tokens = sum(r.completion_tokens for r in results)
    total_tokens = sum(r.total_tokens for r in results)

    tokens_per_sec = total_tokens / duration_s
    tokens_per_min = total_tokens / duration_min if duration_min > 0 else float("nan")
    success_tasks_per_min = success / duration_min if duration_min > 0 else float("nan")
    tasks_per_min = total / duration_min if duration_min > 0 else float("nan")

    avg_tokens_per_req = (total_tokens / success) if success > 0 else float("nan")
    avg_prompt_tokens_per_req = (total_prompt_tokens / success) if success > 0 else float("nan")
    avg_completion_tokens_per_req = (total_completion_tokens / success) if success > 0 else float("nan")

    print("\n=== 壓測結果 ===")
    print(f"總請求: {total}, 成功: {success}, 失敗: {failed}, 成功率: {100*success/total if total else 0:.2f}%")
    print(f"總時長: {duration_s:.2f}s, 吞吐量: {rps:.2f} req/s")
    print("延遲 (ms):")
    print(f"  avg {format_number(avg)} | p50 {format_number(p50)} | p90 {format_number(p90)} | p95 {format_number(p95)} | p99 {format_number(p99)} | p99.9 {format_number(p999)} | max {format_number(mx)}")
    print("LLM Tokens / Tasks:")
    print(
        f"  tokens: total {format_number(float(total_tokens))} (prompt {format_number(float(total_prompt_tokens))}, completion {format_number(float(total_completion_tokens))})"
    )
    print(
        f"  rates: {tokens_per_sec:.2f} tokens/s | {tokens_per_min:.2f} tokens/min | tasks/min {tasks_per_min:.2f} (success {success_tasks_per_min:.2f})"
    )
    print(
        f"  avg per success req: total {avg_tokens_per_req:.2f}, prompt {avg_prompt_tokens_per_req:.2f}, completion {avg_completion_tokens_per_req:.2f}"
    )
    if status_counts:
        print("狀態碼分佈:")
        print(", ".join([f"{code}:{count}" for code, count in sorted(status_counts.items())]))


def parse_args(argv: List[str]):
    import argparse

    parser = argparse.ArgumentParser(description="ngrok 適應性 Chat Completions 壓測器")
    parser.add_argument("--url", default="https://cf26d505c0e6.ngrok-free.app/chat/completions", help="目標 API URL")
    parser.add_argument("--api-key", default=os.getenv("API_KEY", "sk-local-123"), help="Authorization Bearer 金鑰")
    parser.add_argument("--model", default="gpt-oss-120b", help="模型名稱")
    parser.add_argument("--prompt", default="什麼是人工智慧", help="使用者訊息內容")
    parser.add_argument("--temperature", type=float, default=0.7, help="溫度")
    parser.add_argument("--concurrency", type=int, default=5, help="並發 worker 數")
    parser.add_argument("--requests", type=int, default=10, help="總請求數")
    parser.add_argument("--rps", type=float, default=0.0, help="全域節流，每 worker 目標請求數/秒")
    parser.add_argument("--timeout", type=float, default=120.0, help="單請求逾時秒數")
    parser.add_argument("--payload-file", help="覆寫/合併 JSON 載荷檔路徑")
    parser.add_argument("--extra", help="額外 JSON 片段字串，合併到 payload")
    parser.add_argument("--insecure", action="store_true", help="允許不安全 TLS（自簽）")
    parser.add_argument("--verbose", action="store_true", help="詳細錯誤輸出")
    parser.add_argument("--no-warmup", action="store_true", help="跳過 ngrok 預熱")
    return parser.parse_args(argv)


async def main_async(argv: List[str]) -> int:
    if aiohttp is None:
        print("請先安裝 aiohttp：pip install aiohttp", file=sys.stderr)
        return 2

    args = parse_args(argv)
    payload = build_payload(args)
    
    # 改進的連線器設定，適應 ngrok
    connector = aiohttp.TCPConnector(
        ssl=False if args.insecure else None,
        limit=0,  # 無限制連線
        limit_per_host=args.concurrency * 2,  # 每個主機的連線限制
        ttl_dns_cache=300,  # DNS 快取 5 分鐘
        use_dns_cache=True,
        keepalive_timeout=30,  # 保持連線 30 秒
    )
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {args.api_key}",
        "ngrok-skip-browser-warning": "true",
        "Accept": "application/json",
    }

    queue: asyncio.Queue[int] = asyncio.Queue()
    for i in range(args.requests):
        queue.put_nowait(i)

    results: List[Result] = []
    stop_event = asyncio.Event()

    def _handle_sigint(*_):  # noqa: ANN002, ANN003
        if not stop_event.is_set():
            print("\n收到中斷，正在等待當前請求完成...", file=sys.stderr)
            stop_event.set()

    loop = asyncio.get_running_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(s, _handle_sigint)
        except NotImplementedError:
            pass

    started = time.perf_counter()
    async with aiohttp.ClientSession(connector=connector, trust_env=True) as session:
        # ngrok 預熱機制
        if not args.no_warmup:
            base_url = args.url.rsplit('/', 1)[0]  # 移除 /chat/completions 部分
            await ngrok_warmup(session, base_url)
            await asyncio.sleep(0.5)  # 預熱後等待 0.5 秒讓連線穩定
        
        workers = [
            asyncio.create_task(
                worker(
                    name=f"w{i+1}",
                    session=session,
                    url=args.url,
                    headers=headers,
                    payload=payload,
                    queue=queue,
                    results=results,
                    timeout_s=args.timeout,
                    rps=(args.rps if args.rps > 0 else None),
                    worker_id=i,
                )
            )
            for i in range(args.concurrency)
        ]

        await queue.join()
        for w in workers:
            w.cancel()
        # swallow cancellations
        _ = await asyncio.gather(*workers, return_exceptions=True)

    finished = time.perf_counter()
    print_report(results, started, finished)

    if args.verbose and any(r.error for r in results):
        print("\n錯誤樣本：")
        for r in results[:10]:
            if r.error:
                print(f"status={r.status} latency_ms={r.latency_ms:.2f} error={r.error}")

    return 0


def main() -> int:
    try:
        return asyncio.run(main_async(sys.argv[1:]))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())


