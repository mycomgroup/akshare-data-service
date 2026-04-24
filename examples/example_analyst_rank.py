"""
get_analyst_rank() 接口示例

演示如何使用 akshare_data.get_analyst_rank() 获取分析师排名数据。

参数说明:
    start_date: 开始日期，格式 "YYYY-MM-DD"
    end_date:   结束日期，格式 "YYYY-MM-DD"

返回字段: 包含分析师姓名、所属机构、评级次数、评级准确率等
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from akshare_data import get_service
import pandas as pd
from _example_utils import (
    call_with_date_range_fallback,
    fetch_with_retry,
    first_non_empty_by_symbol,
    stable_df,
)


def _build_sample_rank() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"analyst": "张三", "institution": "示例证券", "rating_count": 18, "hit_rate": 0.72},
            {"analyst": "李四", "institution": "示例投研", "rating_count": 15, "hit_rate": 0.69},
            {"analyst": "王五", "institution": "示例基金", "rating_count": 12, "hit_rate": 0.65},
        ]
    )


def _safe_analyst_rank(service, start_date: str, end_date: str):
    # 先按“最近交易日窗口”回溯，提升命中率（缓存经常是最近一段时间有数据）。
    rolling_df, hit_end_date = call_with_date_range_fallback(
        service,
        service.get_analyst_rank,
        max_backtrack=12,
        window_days=365,
    )
    if rolling_df is not None and not rolling_df.empty:
        hit_range = (f"{hit_end_date[:4]}-01-01", hit_end_date) if hit_end_date else None
        return hit_range, stable_df(rolling_df), "analyst_rank(date_fallback)"

    windows = [
        (start_date, end_date),
        ("2024-01-01", "2024-12-31"),
        ("2023-01-01", "2023-12-31"),
        ("2022-01-01", "2022-12-31"),
    ]
    for s, e in windows:
        try:
            df = fetch_with_retry(
                lambda: service.get_analyst_rank(start_date=s, end_date=e),
                retries=1,
            )
            if df is not None and not df.empty:
                return (s, e), stable_df(df), "analyst_rank(window)"
        except Exception:
            continue

    # 部分后端实现会忽略日期参数，最后再尝试一次“无日期全量查询”。
    try:
        full_df = stable_df(fetch_with_retry(lambda: service.get_analyst_rank(), retries=1))
        if full_df is not None and not full_df.empty:
            return None, full_df, "analyst_rank(full_scan)"
    except Exception:
        pass

    # 多 symbol 回退：基于研报数据构建“简版分析师活跃度排名”。
    def _fetch_reports(symbol: str) -> pd.DataFrame:
        return service.get_research_report(
            symbol=symbol,
            start_date="2023-01-01",
            end_date="2026-12-31",
        )

    report_df, hit_symbol = first_non_empty_by_symbol(
        _fetch_reports,
        ["600519", "000001", "300750", "601318", "688981"],
    )
    report_df = stable_df(report_df)
    if report_df is not None and not report_df.empty:
        analyst_col = next((c for c in ("analyst", "分析师", "作者") if c in report_df.columns), None)
        inst_col = next((c for c in ("institution", "所属机构", "机构") if c in report_df.columns), None)
        if analyst_col:
            rank = (
                report_df.groupby(analyst_col, dropna=True)
                .size()
                .reset_index(name="rating_count")
                .sort_values("rating_count", ascending=False, kind="stable")
                .head(20)
                .rename(columns={analyst_col: "analyst"})
                .reset_index(drop=True)
            )
            if inst_col:
                inst_ref = (
                    report_df[[analyst_col, inst_col]]
                    .dropna()
                    .drop_duplicates(subset=[analyst_col], keep="first")
                    .rename(columns={analyst_col: "analyst", inst_col: "institution"})
                )
                rank = rank.merge(inst_ref, on="analyst", how="left")
            return None, rank, f"research_report(symbol_fallback={hit_symbol})"

    return None, _build_sample_rank(), "local_sample"


# ============================================================
# 示例 1: 基本用法 - 获取分析师排名
# ============================================================
def example_basic():
    """基本用法: 获取分析师排名数据"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取分析师排名数据")
    print("=" * 60)

    service = get_service()

    try:
        hit_range, df, source_name = _safe_analyst_rank(service, "2024-01-01", "2024-12-31")
        print(f"命中来源: {source_name}")
        print(f"命中区间: {hit_range}")

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")
        print("\n前10名分析师:")
        print(df.head(10))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: 不同时间区间
# ============================================================
def example_date_ranges():
    """获取不同时间区间的分析师排名"""
    print("\n" + "=" * 60)
    print("示例 2: 不同时间区间分析师排名")
    print("=" * 60)

    service = get_service()

    ranges = [
        ("2024-01-01", "2024-06-30"),
        ("2024-07-01", "2024-12-31"),
    ]

    for start, end in ranges:
        try:
            hit_range, df, source_name = _safe_analyst_rank(service, start, end)
            print(f"\n{start} ~ {end} (命中 {hit_range}, 来源 {source_name}): {len(df)} 位分析师")
            print(df.head(5))
        except Exception as e:
            print(f"\n{start} ~ {end}: 获取失败 - {e}")


# ============================================================
# 示例 3: 筛选特定机构分析师
# ============================================================
def example_filter_institution():
    """筛选特定机构的分析师"""
    print("\n" + "=" * 60)
    print("示例 3: 筛选特定机构分析师")
    print("=" * 60)

    service = get_service()

    try:
        _, df, source_name = _safe_analyst_rank(service, "2024-01-01", "2024-12-31")
        print(f"命中来源: {source_name}")

        print(f"总分析师数: {len(df)}")
        print(f"字段列表: {list(df.columns)}")

        if "institution" in df.columns:
            institutions = df["institution"].unique()
            print(f"\n机构数量: {len(institutions)}")
            print(f"前5个机构: {institutions[:5]}")
        elif "所属机构" in df.columns:
            institutions = df["所属机构"].unique()
            print(f"\n机构数量: {len(institutions)}")
            print(f"前5个机构: {institutions[:5]}")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 4: 分析师排名统计分析
# ============================================================
def example_statistics():
    """对分析师排名进行统计分析"""
    print("\n" + "=" * 60)
    print("示例 4: 分析师排名统计分析")
    print("=" * 60)

    service = get_service()

    try:
        _, df, source_name = _safe_analyst_rank(service, "2024-01-01", "2024-12-31")
        print(f"命中来源: {source_name}")

        print(f"共 {len(df)} 位分析师")
        print(f"字段列表: {list(df.columns)}")

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols:
            print("\n数值字段统计:")
            print(df[numeric_cols].describe())

    except Exception as e:
        print(f"获取数据失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_date_ranges()
    example_filter_institution()
    example_statistics()
