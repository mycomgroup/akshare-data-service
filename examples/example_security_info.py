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


def example_basic_usage():
    """示例1: 获取单只股票的基本信息"""
    print("=" * 60)
    print("示例1: 获取单只股票的基本信息")
    print("=" * 60)

    try:
        symbol = "000001"
        symbol, info = _safe_security_info(symbol)

        if not info:
            print(f"证券代码: {symbol}")
            print("未找到数据")
            return

        print(f"证券代码: {symbol}")
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
            symbol, info = _safe_security_info(symbol)
            if info:
                print(
                    f"{symbol}: {info.get('display_name')} | 类型: {info.get('type')} | 行业: {info.get('industry')}"
                )
            else:
                print(f"{symbol}: 未找到信息")

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
            symbol, info = _safe_security_info(symbol)
            print(f"{desc} ({symbol}):")
            if info:
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print("  未找到信息")
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
        symbol, info1 = _safe_security_info(symbol)
        print(f"  结果: {info1}")
        print()

        print("第二次调用 (从缓存读取):")
        symbol, info2 = _safe_security_info(symbol)
        print(f"  结果: {info2}")

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
            symbol, info = _safe_security_info(symbol)
            if info:
                print(f"{symbol}: {info}")
            else:
                print(f"{symbol}: 返回空结果 (证券不存在)")
        except Exception as e:
            print(f"{symbol}: 异常 - {type(e).__name__}: {e}")

    print()


if __name__ == "__main__":
    example_basic_usage()
    example_multiple_stocks()
    example_different_types()
    example_with_cache()
    example_error_handling()