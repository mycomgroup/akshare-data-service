"""
get_fof_list() 接口示例

演示如何使用 DataService.get_fof_list() 获取FOF基金列表。

接口说明:
- get_fof_list(): 获取全部FOF(Fund of Funds)基金列表
- 无必需参数
- 返回: pd.DataFrame，包含FOF基金代码、名称、类型等字段

使用方式:
    from akshare_data import get_service
    service = get_service()
    df = service.get_fof_list()

注意:
- FOF基金是投资于其他基金的基金
- 该接口返回全市场FOF基金的基本信息
- 采用 Cache-First 策略
"""

import logging
import warnings
from datetime import datetime, timedelta
import pandas as pd

from akshare_data import get_service
from _example_utils import recent_trade_days, stable_df

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)


def _as_dataframe(data, label: str, *, quiet_empty: bool = False) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame):
        print(f"{label}: 返回类型异常，期望 DataFrame，实际 {type(data).__name__}")
        return pd.DataFrame()
    if data.empty and not quiet_empty:
        print(f"{label}: 返回空数据")
    return data


def _rename_by_aliases(df: pd.DataFrame, alias_map: dict[str, list[str]]) -> pd.DataFrame:
    renamed = df.copy()
    for target, aliases in alias_map.items():
        if target in renamed.columns:
            continue
        for alias in aliases:
            if alias in renamed.columns:
                renamed = renamed.rename(columns={alias: target})
                break
    return renamed


def _normalize_fof_fields(df: pd.DataFrame) -> pd.DataFrame:
    normalized = _rename_by_aliases(
        stable_df(df),
        {
            "fund_code": ["基金代码", "代码", "fund_code", "code", "symbol"],
            "fund_name": ["基金名称", "名称", "fund_name", "name"],
            "fund_type": ["基金类型", "类型", "类别", "type"],
            "strategy": ["策略", "strategy", "投资策略"],
            "date": ["日期", "净值日期", "trade_date", "date"],
            "nav": ["单位净值", "最新净值", "净值", "nav"],
        },
    )
    return normalized


def _extract_latest_fof_snapshot(nav_df: pd.DataFrame, fund_code: str) -> dict:
    work = _normalize_fof_fields(nav_df).copy()
    if work.empty:
        return {}
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.sort_values("date", kind="stable")
    last_row = work.iloc[-1]
    return {
        "fund_code": fund_code,
        "fund_name": str(last_row.get("fund_name", "")),
        "date": last_row.get("date"),
        "nav": pd.to_numeric(pd.Series([last_row.get("nav")]), errors="coerce").iloc[0],
        "source": "fof_nav",
    }


def _fetch_fof_with_fallback(service) -> tuple[pd.DataFrame, str | None]:
    try:
        primary = _as_dataframe(service.get_fof_list(), "FOF主接口")
        if not primary.empty:
            return _normalize_fof_fields(primary), "get_fof_list"
    except Exception as exc:
        print(f"FOF主接口异常，尝试回退: {exc}")

    # 回退1: 候选基金代码 + 交易日窗口，探测 fof_nav 可用数据
    candidate_codes = ["006011", "001888", "005156", "161005", "162105", "501018"]
    end_dates = recent_trade_days(service, max_backtrack=12)
    snapshots: list[dict] = []
    for code in candidate_codes:
        if len(snapshots) >= 5:
            break
        for end_date in end_dates:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            start_date = (end_dt - timedelta(days=365)).strftime("%Y-%m-%d")
            try:
                nav_df = _as_dataframe(
                    service.get_fof_nav(
                        fund_code=code,
                        start_date=start_date,
                        end_date=end_date,
                    ),
                    f"fof_nav[{code}@{end_date}]",
                    quiet_empty=True,
                )
                if nav_df.empty:
                    continue
                snapshot = _extract_latest_fof_snapshot(nav_df, fund_code=code)
                if snapshot:
                    snapshots.append(snapshot)
                    break
            except Exception:
                continue
    if snapshots:
        return _normalize_fof_fields(pd.DataFrame(snapshots)), "get_fof_nav(候选代码+日期窗口)"

    # 回退2: 从开放式基金快照中按名称关键词筛选 FOF
    try:
        open_daily = _as_dataframe(service.get_fund_open_daily(), "fund_open_daily回退")
        if not open_daily.empty:
            open_daily = _rename_by_aliases(
                stable_df(open_daily),
                {
                    "fund_code": ["基金代码", "代码", "fund_code", "code", "symbol"],
                    "fund_name": ["基金名称", "名称", "fund_name", "name"],
                    "fund_type": ["基金类型", "类型", "类别", "type"],
                },
            )
            name_col = "fund_name" if "fund_name" in open_daily.columns else None
            type_col = "fund_type" if "fund_type" in open_daily.columns else None
            mask = pd.Series([False] * len(open_daily), index=open_daily.index)
            if name_col:
                mask = mask | open_daily[name_col].astype(str).str.contains("FOF", case=False, na=False)
            if type_col:
                mask = mask | open_daily[type_col].astype(str).str.contains("FOF", case=False, na=False)
            matched = open_daily[mask]
            if not matched.empty:
                return _normalize_fof_fields(matched), "get_fund_open_daily(FOF关键词)"
    except Exception:
        pass
    sample = pd.DataFrame(
        [
            {"fund_code": "006011", "fund_name": "示例稳健FOF", "fund_type": "FOF", "strategy": "稳健配置", "date": "2026-04-24", "nav": 1.128},
            {"fund_code": "001888", "fund_name": "示例平衡FOF", "fund_type": "FOF", "strategy": "平衡配置", "date": "2026-04-24", "nav": 1.064},
            {"fund_code": "005156", "fund_name": "示例养老FOF", "fund_type": "FOF", "strategy": "养老目标", "date": "2026-04-24", "nav": 1.217},
        ]
    )
    return _normalize_fof_fields(sample), "local_sample_fallback"


# ============================================================
# 示例 1: 基本用法 - 获取全部FOF基金列表
# ============================================================
def example_basic():
    """基本用法: 获取全部FOF基金列表"""
    print("=" * 60)
    print("示例 1: 获取全部FOF基金列表")
    print("=" * 60)

    service = get_service()

    try:
        # 获取全部FOF基金列表（含回退策略）
        df, source_name = _fetch_fof_with_fallback(service)
        if df.empty:
            print("示例1: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        # 打印数据形状
        print(f"数据形状: {df.shape}")
        print(f"FOF基金数量: {len(df)}")
        print(f"字段列表: {list(df.columns)}")

        # 打印前10行
        print("\n前10行数据:")
        print(df.head(10).to_string(index=False))

        # 打印后5行
        print("\n后5行数据:")
        print(df.tail().to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: FOF基金类型分析
# ============================================================
def example_fof_type_analysis():
    """分析FOF基金的类型分布"""
    print("\n" + "=" * 60)
    print("示例 2: FOF基金类型分布")
    print("=" * 60)

    service = get_service()

    try:
        df, source_name = _fetch_fof_with_fallback(service)
        if df.empty:
            print("示例2: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        print(f"FOF基金总数: {len(df)}")
        print(f"字段列表: {list(df.columns)}")

        # 查找类型相关列
        type_col = None
        for col in df.columns:
            if "类型" in str(col) or "type" in str(col).lower() or "类别" in str(col):
                type_col = col
                break

        if type_col:
            print("\nFOF基金类型分布:")
            print(df[type_col].value_counts().to_string())
        else:
            print("\n当前数据中未发现基金类型字段")

        # 查找策略相关列
        strategy_col = None
        for col in df.columns:
            if "策略" in str(col) or "strategy" in str(col).lower():
                strategy_col = col
                break

        if strategy_col:
            print("\nFOF策略分布:")
            print(df[strategy_col].value_counts().head(10).to_string())

    except Exception as e:
        print(f"分析失败: {e}")


# ============================================================
# 示例 3: 筛选特定FOF基金
# ============================================================
def example_filter_fof():
    """在FOF列表中查找特定基金"""
    print("\n" + "=" * 60)
    print("示例 3: 查找特定FOF基金")
    print("=" * 60)

    service = get_service()

    # 示例FOF基金代码 (实际代码请查询)
    target_keywords = ["养老", "配置", "稳健"]

    try:
        df, source_name = _fetch_fof_with_fallback(service)
        if df.empty:
            print("示例3: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        print(f"FOF基金总数: {len(df)}")

        # 查找名称列
        name_col = None
        for col in df.columns:
            if "名称" in str(col) or "name" in str(col).lower():
                name_col = col
                break

        if name_col:
            for keyword in target_keywords:
                matched = df[df[name_col].astype(str).str.contains(keyword, na=False)]
                print(f"\n包含'{keyword}'的FOF基金: {len(matched)} 只")
                if not matched.empty:
                    print(matched.head(5).to_string(index=False))
        else:
            print("未找到基金名称字段")
            print(f"可用字段: {list(df.columns)}")

    except Exception as e:
        print(f"查找失败: {e}")


# ============================================================
# 示例 4: FOF基金统计信息
# ============================================================
def example_fof_statistics():
    """获取FOF基金的统计信息"""
    print("\n" + "=" * 60)
    print("示例 4: FOF基金统计信息")
    print("=" * 60)

    service = get_service()

    try:
        df, source_name = _fetch_fof_with_fallback(service)
        if df.empty:
            print("示例4: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        print(f"FOF基金总数: {len(df)}")
        print(f"数据字段: {list(df.columns)}")

        # 查找数值型字段进行统计
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if numeric_cols:
            for col in numeric_cols[:3]:  # 只显示前3个数值列
                print(f"\n{col} 统计:")
                print(f"  平均值: {df[col].mean():.4f}")
                print(f"  中位数: {df[col].median():.4f}")
                print(f"  最大值: {df[col].max():.4f}")
                print(f"  最小值: {df[col].min():.4f}")
        else:
            print("\n当前数据中无数值型字段")

    except Exception as e:
        print(f"统计失败: {e}")


# ============================================================
# 示例 5: 获取前N只FOF基金
# ============================================================
def example_top_fofs():
    """获取FOF基金列表并显示前N只"""
    print("\n" + "=" * 60)
    print("示例 5: 查看前N只FOF基金")
    print("=" * 60)

    service = get_service()

    try:
        df, source_name = _fetch_fof_with_fallback(service)
        if df.empty:
            print("示例5: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        print(f"FOF基金总数: {len(df)}")
        print("\n前20只FOF基金:")
        print(df.head(20).to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_fof_type_analysis()
    example_filter_fof()
    example_fof_statistics()
    example_top_fofs()
