"""
get_st_stocks() 接口示例

演示如何使用 akshare_data.get_st_stocks() 获取 ST 股票列表。

ST 股票是指被实施特别处理的股票，通常因为连续亏损或其他异常情况。
常见的 ST 类型包括:
  - ST: 其他特别处理
  - *ST: 退市风险警示

参数说明:
  - 无参数

返回字段: code, display_name (具体字段以实际返回为准)
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd
import akshare as ak

from akshare_data import get_st_stocks, get_securities_list


def _mock_st_stocks():
    return pd.DataFrame(
        {
            "code": ["600234", "000971", "002569", "600568", "300044"],
            "display_name": ["*ST科新", "ST高升", "*ST步森", "ST中珠", "ST赛为"],
        }
    )


def _fetch_st_stocks():
    try:
        df = get_st_stocks()
        if df is not None and not df.empty:
            return df
    except Exception as e:
        print(f"实时接口异常: {e}")
    try:
        df = ak.stock_zh_a_st_em()
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    print("[ST接口不可用或无数据，使用演示数据]")
    return _mock_st_stocks()


# ============================================================
# 示例 1: 基本用法 - 获取全部 ST 股票列表
# ============================================================
def example_basic():
    """基本用法: 获取全部 ST 股票列表"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取全部 ST 股票列表")
    print("=" * 60)

    try:
        df = _fetch_st_stocks()

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10只ST股票:")
        print(df.head(10))

        print("\n后5行数据:")
        print(df.tail())

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: 统计 ST 股票数量
# ============================================================
def example_count():
    """统计 ST 股票数量"""
    print("\n" + "=" * 60)
    print("示例 2: 统计 ST 股票数量")
    print("=" * 60)

    try:
        df = _fetch_st_stocks()

        total_count = len(df)
        print(f"当前 ST 股票总数: {total_count} 只")

        if "display_name" in df.columns:
            star_st = df[df["display_name"].str.contains(r"\*ST", na=False)]
            normal_st = df[~df["display_name"].str.contains(r"\*ST", na=False)]

            print(f"  *ST 股票 (退市风险警示): {len(star_st)} 只")
            print(f"  ST 股票 (其他特别处理): {len(normal_st)} 只")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 3: 查看 ST 股票详细信息
# ============================================================
def example_details():
    """查看 ST 股票详细信息"""
    print("\n" + "=" * 60)
    print("示例 3: 查看 ST 股票详细信息")
    print("=" * 60)

    try:
        df = _fetch_st_stocks()

        print(f"共 {len(df)} 只 ST 股票\n")

        print("前20只ST股票详细信息:")
        print(df.head(20).to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 4: 筛选特定板块的 ST 股票
# ============================================================
def example_filter_by_board():
    """按板块筛选 ST 股票"""
    print("\n" + "=" * 60)
    print("示例 4: 按板块筛选 ST 股票")
    print("=" * 60)

    try:
        df = _fetch_st_stocks()

        code_col = "code" if "code" in df.columns else "symbol"

        sh_st = df[df[code_col].astype(str).str.startswith("60")]
        print(f"沪市主板 ST: {len(sh_st)} 只")
        if not sh_st.empty:
            print(sh_st.head(5))

        sz_st = df[df[code_col].astype(str).str.startswith("00")]
        print(f"\n深市主板 ST: {len(sz_st)} 只")
        if not sz_st.empty:
            print(sz_st.head(5))

        cyb_st = df[df[code_col].astype(str).str.startswith("30")]
        print(f"\n创业板 ST: {len(cyb_st)} 只")
        if not cyb_st.empty:
            print(cyb_st.head(5))

        kcb_st = df[df[code_col].astype(str).str.startswith("68")]
        print(f"\n科创板 ST: {len(kcb_st)} 只")
        if not kcb_st.empty:
            print(kcb_st.head(5))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 5: 结合证券列表使用
# ============================================================
def example_with_securities_list():
    """结合证券列表获取更完整的 ST 股票信息"""
    print("\n" + "=" * 60)
    print("示例 5: 结合证券列表使用")
    print("=" * 60)

    try:
        st_df = _fetch_st_stocks()

        all_stocks = get_securities_list()

        if all_stocks.empty:
            print("无法获取股票列表")
            return

        code_col = "code" if "code" in st_df.columns else "symbol"
        st_codes = st_df[code_col].astype(str).tolist()

        all_code_col = "code" if "code" in all_stocks.columns else "symbol"
        st_info = all_stocks[all_stocks[all_code_col].astype(str).isin(st_codes)]

        print(f"ST 股票数量: {len(st_df)}")
        print(f"成功匹配证券信息的数量: {len(st_info)}")

        if not st_info.empty:
            print("\nST 股票详细信息:")
            print(st_info.head(10).to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 6: 导出 ST 股票列表
# ============================================================
def example_export():
    """将 ST 股票列表导出为 CSV 文件"""
    print("\n" + "=" * 60)
    print("示例 6: 导出 ST 股票列表")
    print("=" * 60)

    try:
        df = _fetch_st_stocks()

        print(f"获取到 {len(df)} 只 ST 股票")
        print(f"字段列表: {list(df.columns)}")

        print("\n前5行预览:")
        print(df.head())

    except Exception as e:
        print(f"获取数据失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_count()
    example_details()
    example_filter_by_board()
    example_with_securities_list()
    example_export()