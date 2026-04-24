"""
get_security_info() 接口使用示例

该接口用于获取单只证券的基本信息，包括：
- code: 证券代码
- display_name: 显示名称
- type: 证券类型 (stock/index/etf 等)
- start_date: 上市日期
- industry: 所属行业

导入方式: from akshare_data import get_security_info

注意: 该接口底层调用 akshare 的 stock_individual_info_em(symbol)。
      如遇网络连接超时或连接错误，请检查网络状态后重试。
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
import akshare as ak

from akshare_data import get_security_info
from _example_utils import fetch_with_retry, normalize_symbol_input

logging.getLogger("akshare_data").setLevel(logging.ERROR)


<<<<<<< HEAD
def _mock_security_info(symbol):
    return {
        "code": symbol,
        "display_name": "演示股票",
        "type": "stock",
        "start_date": "2000-01-01",
        "industry": "演示行业",
    }


def _safe_security_info(symbol: str):
    code = normalize_symbol_input(symbol)
    try:
        result = fetch_with_retry(lambda: get_security_info(code), retries=2)
        return code, result
    except Exception:
        return code, _mock_security_info(code)
=======
DEFAULT_FALLBACK_SYMBOLS = [
    "000001",
    "600519",
    "000300",
    "510300",
    "159915",
]


def _candidate_symbols(symbol: str, fallback_symbols: list[str] | None = None) -> list[str]:
    raw = (symbol or "").strip()
    candidates: list[str] = []
    if raw:
        candidates.append(raw)
        if "." not in raw and len(raw) == 6 and raw.isdigit():
            if raw.startswith(("0", "3")):
                candidates.extend([f"{raw}.sz", f"sz{raw}"])
            elif raw.startswith(("6", "9")):
                candidates.extend([f"{raw}.sh", f"sh{raw}"])
    candidates.extend(fallback_symbols or DEFAULT_FALLBACK_SYMBOLS)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def _safe_security_info(symbol: str, *, retries: int = 2):
    tried: list[str] = []
    errors: list[str] = []
    seen_codes: set[str] = set()

    for candidate in _candidate_symbols(symbol):
        try:
            code = normalize_symbol_input(candidate)
            if code in seen_codes:
                continue
            seen_codes.add(code)
            tried.append(code)
            info = fetch_with_retry(lambda: get_security_info(code), retries=retries)
            if info:
                return code, info, tried, errors
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
            continue

    return None, None, tried, errors


def _print_info_brief(symbol: str, info: dict):
    print(f"命中代码: {symbol}")
    print(
        "摘要: "
        f"{info.get('display_name', '-')}"
        f" | 类型: {info.get('type', '-')}"
        f" | 行业: {info.get('industry', '-')}"
        f" | 上市日期: {info.get('start_date', '-')}"
    )
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d


def example_basic_usage():
    """示例1: 获取单只股票的基本信息"""
    print("=" * 60)
    print("示例1: 获取单只股票的基本信息")
    print("=" * 60)

    try:
<<<<<<< HEAD
        symbol = "000001"
        symbol, info = _safe_security_info(symbol)
=======
        # symbol: 证券代码，支持多种格式 (如 "000001", "000001.sz", "600519")
        symbol = "000001"  # 平安银行
        hit_symbol, info, tried, errors = _safe_security_info(symbol)
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d

        if not info or not hit_symbol:
            print(f"输入代码: {symbol}")
            print("未找到数据")
            print(f"候选代码: {', '.join(_candidate_symbols(symbol))}")
            if errors:
                print(f"最近错误: {errors[-1]}")
            return

<<<<<<< HEAD
        print(f"证券代码: {symbol}")
=======
        # 打印返回的完整字典
        print(f"输入代码: {symbol}")
        _print_info_brief(hit_symbol, info)
        print(f"尝试顺序: {', '.join(tried)}")
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
        print(f"返回数据: {info}")
        print()

        print(f"  代码: {info.get('code')}")
        print(f"  名称: {info.get('display_name')}")
        print(f"  类型: {info.get('type')}")
        print(f"  上市日期: {info.get('start_date')}")
        print(f"  行业: {info.get('industry')}")

    except Exception as e:
        err_msg = str(e).lower()
        if "connection" in err_msg or "timeout" in err_msg or "network" in err_msg:
            print(f"网络连接错误: {e}")
            print("提示: 请检查网络状态，或稍后重试")
        else:
            print(f"获取证券信息时出错: {e}")

    print()


def example_multiple_stocks():
    """示例2: 批量获取多只股票信息"""
    print("=" * 60)
    print("示例2: 批量获取多只股票信息")
    print("=" * 60)

    stocks = [
        "000001",
        "600519",
        "000858",
        "300750",
    ]

    try:
        for symbol in stocks:
            hit_symbol, info, _, errors = _safe_security_info(symbol)
            if info and hit_symbol:
                print(
                    f"{symbol} -> {hit_symbol}: {info.get('display_name')} | "
                    f"类型: {info.get('type')} | 行业: {info.get('industry')}"
                )
            else:
                msg = f"{symbol}: 未找到信息"
                if errors:
                    msg += f" | 最近错误: {errors[-1]}"
                print(msg)

    except Exception as e:
        err_msg = str(e).lower()
        if "connection" in err_msg or "timeout" in err_msg or "network" in err_msg:
            print(f"网络连接错误: {e}")
            print("提示: 请检查网络状态，或稍后重试")
        else:
            print(f"批量获取股票信息时出错: {e}")

    print()


def example_different_types():
    """示例3: 获取不同类型证券的信息 (股票/指数/ETF)"""
    print("=" * 60)
    print("示例3: 获取不同类型证券的信息")
    print("=" * 60)

    securities = {
        "000001": "股票 - 平安银行",
        "000300": "指数 - 沪深300",
        "510300": "ETF - 沪深300ETF",
    }

    try:
        for symbol, desc in securities.items():
            hit_symbol, info, tried, errors = _safe_security_info(symbol)
            print(f"{desc} ({symbol}):")
            if info and hit_symbol:
                print(f"  命中代码: {hit_symbol}")
                print(f"  尝试顺序: {', '.join(tried)}")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print("  未找到信息")
                print(f"  候选代码: {', '.join(_candidate_symbols(symbol))}")
                if errors:
                    print(f"  最近错误: {errors[-1]}")
            print()

    except Exception as e:
        err_msg = str(e).lower()
        if "connection" in err_msg or "timeout" in err_msg or "network" in err_msg:
            print(f"网络连接错误: {e}")
            print("提示: 请检查网络状态，或稍后重试")
        else:
            print(f"获取证券信息时出错: {e}")


def example_with_cache():
    """示例4: 演示缓存机制 (第二次调用会从缓存读取)"""
    print("=" * 60)
    print("示例4: 演示缓存机制")
    print("=" * 60)

    symbol = "000001"

    try:
        print("第一次调用 (从数据源获取):")
        hit_symbol1, info1, tried1, errors1 = _safe_security_info(symbol)
        print(f"  结果: {info1}")
        print(f"  命中代码: {hit_symbol1}")
        print(f"  尝试顺序: {', '.join(tried1)}")
        if errors1:
            print(f"  最近错误: {errors1[-1]}")
        print()

        print("第二次调用 (从缓存读取):")
        hit_symbol2, info2, tried2, errors2 = _safe_security_info(symbol)
        print(f"  结果: {info2}")
        print(f"  命中代码: {hit_symbol2}")
        print(f"  尝试顺序: {', '.join(tried2)}")
        if errors2:
            print(f"  最近错误: {errors2[-1]}")

    except Exception as e:
        err_msg = str(e).lower()
        if "connection" in err_msg or "timeout" in err_msg or "network" in err_msg:
            print(f"网络连接错误: {e}")
            print("提示: 请检查网络状态，或稍后重试")
        else:
            print(f"获取证券信息时出错: {e}")

    print()


def example_error_handling():
    """示例5: 错误处理演示"""
    print("=" * 60)
    print("示例5: 错误处理演示")
    print("=" * 60)

    invalid_symbols = ["999999", "ABCDEF", ""]

    for symbol in invalid_symbols:
        try:
            hit_symbol, info, tried, errors = _safe_security_info(symbol)
            if info and hit_symbol:
                print(f"{symbol} -> {hit_symbol}: {info}")
            else:
                print(f"{symbol}: 返回空结果 (证券不存在或网络波动)")
                print(f"  候选代码: {', '.join(_candidate_symbols(symbol))}")
                print(f"  尝试顺序: {', '.join(tried) if tried else '-'}")
                if errors:
                    print(f"  最近错误: {errors[-1]}")
        except Exception as e:
            print(f"{symbol}: 异常 - {type(e).__name__}: {e}")

    print()


if __name__ == "__main__":
    example_basic_usage()
    example_multiple_stocks()
    example_different_types()
    example_with_cache()
    example_error_handling()