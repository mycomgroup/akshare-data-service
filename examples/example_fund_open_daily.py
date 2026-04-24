"""get_fund_open_daily() 接口示例"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
<<<<<<< HEAD
=======
import warnings
from datetime import datetime, timedelta
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
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


def _normalize_open_fund_fields(df: pd.DataFrame) -> pd.DataFrame:
    normalized = _rename_by_aliases(
        stable_df(df),
        {
            "fund_code": ["基金代码", "代码", "fund_code", "code", "symbol"],
            "fund_name": ["基金名称", "名称", "fund_name", "name"],
            "fund_type": ["基金类型", "类型", "类别", "type"],
            "date": ["净值日期", "日期", "trade_date", "date"],
            "nav": ["单位净值", "最新净值", "净值", "nav", "value"],
            "acc_nav": ["累计净值", "acc_nav"],
        },
    )
    return normalized


def _extract_latest_open_fund_snapshot(nav_df: pd.DataFrame, fund_code: str) -> dict:
    work = _normalize_open_fund_fields(nav_df).copy()
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
        "acc_nav": pd.to_numeric(pd.Series([last_row.get("acc_nav")]), errors="coerce").iloc[0],
        "source": "fund_open_nav",
    }


def _fetch_open_daily_with_fallback(service) -> tuple[pd.DataFrame, str | None]:
    try:
        primary = _as_dataframe(service.get_fund_open_daily(), "开放基金主接口")
        if not primary.empty:
            return _normalize_open_fund_fields(primary), "get_fund_open_daily"
    except Exception as exc:
        print(f"开放基金主接口异常，尝试回退: {exc}")

    # 回退1: 候选基金代码 + 日期窗口，从 fund_open_nav 组装最新快照
    candidate_codes = ["110011", "000001", "161725", "163406", "519674", "005827"]
    end_dates = recent_trade_days(service, max_backtrack=12)
    window_days_options = (30, 120, 365)
    snapshots: list[dict] = []
    for code in candidate_codes:
        if len(snapshots) >= 6:
            break
        hit = False
        for end_date in end_dates:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            for window_days in window_days_options:
                start_date = (end_dt - timedelta(days=window_days)).strftime("%Y-%m-%d")
                try:
                    nav_df = _as_dataframe(
                        service.get_fund_open_nav(
                            fund_code=code,
                            start_date=start_date,
                            end_date=end_date,
                        ),
                        f"fund_open_nav[{code}@{end_date}]",
                        quiet_empty=True,
                    )
                    if nav_df.empty:
                        continue
                    snapshot = _extract_latest_open_fund_snapshot(nav_df, fund_code=code)
                    if snapshot:
                        snapshots.append(snapshot)
                        hit = True
                        break
                except Exception:
                    continue
            if hit:
                break
    if snapshots:
        return _normalize_open_fund_fields(pd.DataFrame(snapshots)), "get_fund_open_nav(候选代码+日期窗口)"

    # 回退2: 候选代码调用 fund_open_info 兜底（部分环境只有元信息）
    info_rows: list[dict] = []
    for code in candidate_codes:
        try:
            info = service.get_fund_open_info(fund_code=code)
            if isinstance(info, dict) and info:
                info_rows.append(info | {"fund_code": code, "source": "fund_open_info"})
        except Exception:
            continue
    if info_rows:
        return _normalize_open_fund_fields(pd.DataFrame(info_rows)), "get_fund_open_info(候选代码)"
    sample = pd.DataFrame(
        [
            {"fund_code": "110011", "fund_name": "示例蓝筹精选", "fund_type": "混合型", "date": "2026-04-24", "nav": 1.523, "acc_nav": 2.468},
            {"fund_code": "161725", "fund_name": "示例白酒指数", "fund_type": "指数型", "date": "2026-04-24", "nav": 1.947, "acc_nav": 3.102},
            {"fund_code": "000001", "fund_name": "示例成长基金", "fund_type": "股票型", "date": "2026-04-24", "nav": 1.338, "acc_nav": 2.011},
        ]
    )
    return _normalize_open_fund_fields(sample), "local_sample_fallback"


# ============================================================
# 示例 1: 基本用法 - 获取全部开放式基金每日净值列表
# ============================================================
def example_basic():
    """基本用法: 获取全部开放式基金每日净值列表"""
    print("=" * 60)
    print("示例 1: 获取全部开放式基金每日净值列表")
    print("=" * 60)

    service = get_service()

    try:
        # 获取开放式基金净值快照（含回退策略）
        df, source_name = _fetch_open_daily_with_fallback(service)
        if df.empty:
            print("示例1: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        # 打印数据形状
        print(f"数据形状: {df.shape}")
        print(f"基金数量: {len(df)}")
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
# 示例 2: 筛选特定类型的基金
# ============================================================
def example_filter_by_type():
    """获取基金列表后按类型筛选"""
    print("\n" + "=" * 60)
    print("示例 2: 按基金类型筛选")
    print("=" * 60)

    service = get_service()

    try:
        df, source_name = _fetch_open_daily_with_fallback(service)
        if df.empty:
            print("示例2: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        # 尝试按常见字段筛选 (字段名可能因数据源而异)
        print(f"总基金数量: {len(df)}")
        print(f"字段列表: {list(df.columns)}")

        # 如果存在基金类型列，进行筛选演示
        type_col = None
        for col in df.columns:
            if "类型" in str(col) or "type" in str(col).lower() or "类别" in str(col):
                type_col = col
                break

        if type_col:
            print("\n基金类型分布:")
            print(df[type_col].value_counts().head(10))
        else:
            print("\n当前数据源返回的字段中未发现基金类型列")
            print("可尝试按其他字段筛选，如净值范围等")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 3: 查找特定基金
# ============================================================
def example_find_specific_fund():
    """在基金列表中查找特定基金"""
    print("\n" + "=" * 60)
    print("示例 3: 查找特定基金")
    print("=" * 60)

    service = get_service()

    # 要查找的基金代码
    target_code = "110011"

    try:
        df, source_name = _fetch_open_daily_with_fallback(service)
        if df.empty:
            print("示例3: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        print(f"在 {len(df)} 只基金中查找代码: {target_code}")

        # 尝试在不同列中查找基金代码
        code_col = None
        for col in df.columns:
            if "代码" in str(col) or "code" in str(col).lower() or "symbol" in str(col).lower():
                code_col = col
                break

        if code_col:
            matched = df[df[code_col].astype(str).str.contains(target_code, na=False)]
            if not matched.empty:
                print("\n找到匹配基金:")
                print(matched.to_string(index=False))
            else:
                print(f"\n未找到代码为 {target_code} 的基金")
        else:
            print("当前数据未包含基金代码字段，无法按代码筛选")
            print("\n显示前5行数据供参考:")
            print(df.head().to_string(index=False))

    except Exception as e:
        print(f"查找失败: {e}")


# ============================================================
# 示例 4: 净值统计分析
# ============================================================
def example_nav_statistics():
    """对基金净值进行简单统计分析"""
    print("\n" + "=" * 60)
    print("示例 4: 净值统计分析")
    print("=" * 60)

    service = get_service()

    try:
        df, source_name = _fetch_open_daily_with_fallback(service)
        if df.empty:
            print("示例4: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        # 查找净值相关列
        nav_col = None
        for col in df.columns:
            if "净值" in str(col) or "nav" in str(col).lower() or "value" in str(col).lower():
                series = pd.to_numeric(df[col], errors="coerce")
                if series.notna().any():
                    nav_col = col
                    break

        if nav_col:
            nav = pd.to_numeric(df[nav_col], errors="coerce").dropna()
            if nav.empty:
                print(f"{nav_col} 无有效数值")
                return
            print(f"使用净值列: {nav_col}")
            print("\n净值统计:")
            print(f"  平均值: {nav.mean():.4f}")
            print(f"  中位数: {nav.median():.4f}")
            print(f"  最大值: {nav.max():.4f}")
            print(f"  最小值: {nav.min():.4f}")

            # 净值分布
            print("\n净值分布 (分位数):")
            print(nav.quantile([0.1, 0.25, 0.5, 0.75, 0.9]).to_string())
        else:
            print("当前数据中未发现数值型净值字段")
            print(f"可用字段: {list(df.columns)}")

    except Exception as e:
        print(f"统计分析失败: {e}")


# ============================================================
# 示例 5: 获取多只基金的净值对比
# ============================================================
def example_multiple_funds_comparison():
    """对比多只基金的净值数据"""
    print("\n" + "=" * 60)
    print("示例 5: 多只基金净值对比")
    print("=" * 60)

    service = get_service()

    # 目标基金代码列表
    target_codes = ["110011", "000001", "161725"]

    try:
        df, source_name = _fetch_open_daily_with_fallback(service)
        if df.empty:
            print("示例5: 多级回退后仍无数据")
            return
        print(f"命中来源: {source_name}")

        print(f"基金代码列表: {target_codes}")
        print(f"总基金数量: {len(df)}")

        # 查找代码列
        code_col = None
        for col in df.columns:
            if "代码" in str(col) or "code" in str(col).lower():
                code_col = col
                break

        if code_col:
            for code in target_codes:
                matched = df[df[code_col].astype(str) == code]
                if not matched.empty:
                    print(f"\n基金 {code}:")
                    print(matched.to_string(index=False))
                else:
                    print(f"\n基金 {code}: 未找到")
        else:
            print("未找到基金代码字段，显示前5行:")
            print(df.head().to_string(index=False))

    except Exception as e:
        print(f"对比分析失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_filter_by_type()
    example_find_specific_fund()
    example_nav_statistics()
    example_multiple_funds_comparison()
