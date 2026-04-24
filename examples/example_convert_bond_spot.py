"""get_convert_bond_spot() 接口示例

演示如何使用 DataService 获取可转债实时行情数据。

接口说明:
- get_convert_bond_spot() - 获取可转债实时行情
  - 无必需参数
  - 返回: DataFrame - 包含所有可转债的实时行情数据

该接口目前仅在 LixingerAdapter 中实现，如需使用需配置 LIXINGER_TOKEN。
若数据源不可用，示例中会展示期望的数据格式。

注意: 该接口返回实时行情数据，不支持缓存，每次调用都会从数据源获取最新数据。

典型返回字段:
- bond_code: 可转债代码
- bond_name: 可转债名称
- current_price: 当前价格
- change_percent: 涨跌幅 (%)
- volume: 成交量
- amount: 成交额
- premium_rate: 溢价率
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd
import akshare as ak
from akshare_data import get_service


def _mock_spot_data():
    """返回模拟的可转债实时行情数据用于演示"""
    return pd.DataFrame({
        "bond_code": ["127045", "110059", "123107", "113050", "128143", "113052"],
        "bond_name": ["牧原转债", "南航转债", "蓝盾转债", "南银转债", "锋龙转债", "兴业转债"],
        "current_price": [120.50, 117.80, 106.20, 100.50, 109.10, 112.30],
        "change_percent": [1.25, -0.85, 2.15, 0.35, -1.20, 0.75],
        "volume": [52000, 125000, 89000, 45000, 32000, 67000],
        "amount": [6266000, 14725000, 9451800, 4522500, 3491200, 7524100],
        "premium_rate": [15.2, -2.5, 35.8, 8.3, 22.1, 18.5],
    })


def _fetch_convert_bond_spot():
    service = get_service()
    try:
        df = service.get_convert_bond_spot()
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    try:
        df = ak.bond_zh_cov_snapshot()
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    print("[可转债实时接口不可用，使用演示数据]")
    return _mock_spot_data()


# ============================================================
# 示例 1: 基本用法 - 获取可转债实时行情
# ============================================================
def example_basic():
    """基本用法: 获取可转债实时行情数据"""
    print("=" * 60)
    print("示例 1: 获取可转债实时行情")
    print("=" * 60)

    try:
        df = _fetch_convert_bond_spot()

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10行数据:")
        print(df.head(10).to_string(index=False))

        print(f"\n共获取 {len(df)} 只可转债的实时行情")

    except Exception as e:
        print(f"获取数据失败: {e}")
        print("使用演示数据:")
        df = _mock_spot_data()
        print(df.head(10).to_string(index=False))


# ============================================================
# 示例 2: 涨幅榜和跌幅榜
# ============================================================
def example_top_movers():
    """查看可转债涨跌幅排行"""
    print("\n" + "=" * 60)
    print("示例 2: 可转债涨跌幅排行")
    print("=" * 60)

    try:
        df = _fetch_convert_bond_spot()

        change_col = None
        for col in ["change_percent", "涨跌幅", "pct_change"]:
            if col in df.columns:
                change_col = col
                break

        if change_col is None:
            print("数据中无涨跌幅字段")
            return

        df[change_col] = pd.to_numeric(df[change_col], errors="coerce")

        price_col = None
        for col in ["current_price", "价格", "price"]:
            if col in df.columns:
                price_col = col
                break

        code_col = None
        for col in ["bond_code", "代码", "code"]:
            if col in df.columns:
                code_col = col
                break

        name_col = None
        for col in ["bond_name", "名称", "name"]:
            if col in df.columns:
                name_col = col
                break

        display_cols = [c for c in [code_col, name_col, price_col, change_col] if c]

        print("\n涨幅榜 TOP 5:")
        top_gainers = df.nlargest(5, change_col)
        print(top_gainers[display_cols].to_string(index=False))

        print("\n跌幅榜 TOP 5:")
        top_losers = df.nsmallest(5, change_col)
        print(top_losers[display_cols].to_string(index=False))

    except Exception as e:
        print(f"分析失败: {e}")


# ============================================================
# 示例 3: 筛选活跃可转债
# ============================================================
def example_active_bonds():
    """筛选成交量活跃的可转债"""
    print("\n" + "=" * 60)
    print("示例 3: 筛选活跃可转债")
    print("=" * 60)

    try:
        df = _fetch_convert_bond_spot()

        vol_col = None
        for col in ["volume", "成交量", "vol"]:
            if col in df.columns:
                vol_col = col
                break

        amt_col = None
        for col in ["amount", "成交额", "turnover"]:
            if col in df.columns:
                amt_col = col
                break

        if vol_col is None:
            print("数据中无成交量字段")
            return

        df[vol_col] = pd.to_numeric(df[vol_col], errors="coerce")
        if amt_col and amt_col in df.columns:
            df[amt_col] = pd.to_numeric(df[amt_col], errors="coerce")

        active_threshold = 50000
        active_bonds = df[df[vol_col] > active_threshold].copy()
        active_bonds = active_bonds.sort_values(vol_col, ascending=False)

        print(f"\n成交量超过 {active_threshold} 的可转债: {len(active_bonds)} 只")

        price_col = None
        for col in ["current_price", "价格", "price"]:
            if col in df.columns:
                price_col = col
                break

        change_col = None
        for col in ["change_percent", "涨跌幅", "pct_change"]:
            if col in df.columns:
                change_col = col
                break

        display_cols = [c for c in ["bond_code", "bond_name", price_col, vol_col, amt_col, change_col] if c and c in df.columns]

        if not active_bonds.empty:
            print(active_bonds[display_cols].head(10).to_string(index=False))
        else:
            print("暂无高成交量可转债")

    except Exception as e:
        print(f"筛选失败: {e}")


# ============================================================
# 示例 4: 价格区间分析
# ============================================================
def example_price_range():
    """按价格区间统计可转债分布"""
    print("\n" + "=" * 60)
    print("示例 4: 价格区间分析")
    print("=" * 60)

    try:
        df = _fetch_convert_bond_spot()

        price_col = None
        for col in ["current_price", "价格", "price"]:
            if col in df.columns:
                price_col = col
                break

        if price_col is None:
            print("数据中无当前价格字段")
            return

        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")

        bins = [0, 100, 110, 120, 130, 150, float("inf")]
        labels = ["<100", "100-110", "110-120", "120-130", "130-150", ">150"]
        df["price_range"] = pd.cut(df[price_col], bins=bins, labels=labels)

        print("\n全市场可转债价格分布:")
        distribution = df["price_range"].value_counts().sort_index()
        for range_label, count in distribution.items():
            percentage = count / len(df) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {range_label:8s}: {count:4d} 只 ({percentage:5.1f}%) {bar}")

        print("\n价格统计:")
        print(f"  平均价格: {df[price_col].mean():.2f}")
        print(f"  中位数: {df[price_col].median():.2f}")
        print(f"  最低: {df[price_col].min():.2f}")
        print(f"  最高: {df[price_col].max():.2f}")

    except Exception as e:
        print(f"分析失败: {e}")


# ============================================================
# 示例 5: 查找特定可转债行情
# ============================================================
def example_find_bond():
    """查找特定可转债的实时行情"""
    print("\n" + "=" * 60)
    print("示例 5: 查找特定可转债行情")
    print("=" * 60)

    try:
        df = _fetch_convert_bond_spot()

        bond_code = "127045"
        bond_name = "牧原转债"

        print(f"\n查找可转债: {bond_code} ({bond_name})")

        code_col = None
        for col in ["bond_code", "代码", "code"]:
            if col in df.columns:
                code_col = col
                break

        name_col = None
        for col in ["bond_name", "名称", "name"]:
            if col in df.columns:
                name_col = col
                break

        if code_col:
            bond = df[df[code_col] == bond_code]
            if bond.empty and name_col and name_col in df.columns:
                bond = df[df[name_col] == bond_name]

            if not bond.empty:
                print("\n行情数据:")
                print(bond.to_string(index=False))

                change_col = None
                for col in ["change_percent", "涨跌幅", "pct_change"]:
                    if col in bond.columns:
                        change_col = col
                        break

                premium_col = None
                for col in ["premium_rate", "溢价率"]:
                    if col in bond.columns:
                        premium_col = col
                        break

                if change_col and premium_col:
                    change = float(bond[change_col].iloc[0])
                    premium = float(bond[premium_col].iloc[0])

                    print("\n分析:")
                    print(f"  今日涨跌: {change:+.2f}%")
                    print(f"  当前溢价率: {premium:.2f}%")

                    if change > 3:
                        print("  状态: 今日涨幅较大，关注是否追高")
                    elif change < -3:
                        print("  状态: 今日跌幅较大，可能存在机会")

                    if premium < 0:
                        print("  状态: 负溢价，存在转股套利空间")
                    elif premium < 10:
                        print("  状态: 低溢价，股性较强")
                    else:
                        print("  状态: 高溢价，债性较强")
            else:
                print(f"  未找到代码为 {bond_code} 的可转债")
        else:
            print("数据中无可转债代码字段")

    except Exception as e:
        print(f"查询失败: {e}")


# ============================================================
# 示例 6: 综合筛选 - 活跃且低估的可转债
# ============================================================
def example_comprehensive_filter():
    """综合筛选: 寻找活跃且低估的可转债"""
    print("\n" + "=" * 60)
    print("示例 6: 综合筛选 - 活跃且低估的可转债")
    print("=" * 60)

    try:
        df = _fetch_convert_bond_spot()

        price_col = None
        for col in ["current_price", "价格", "price"]:
            if col in df.columns:
                price_col = col
                break

        vol_col = None
        for col in ["volume", "成交量", "vol"]:
            if col in df.columns:
                vol_col = col
                break

        change_col = None
        for col in ["change_percent", "涨跌幅", "pct_change"]:
            if col in df.columns:
                change_col = col
                break

        premium_col = None
        for col in ["premium_rate", "溢价率"]:
            if col in df.columns:
                premium_col = col
                break

        for col in [price_col, vol_col, change_col, premium_col]:
            if col and col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if not all([price_col, vol_col, premium_col]) or price_col not in df.columns or vol_col not in df.columns or premium_col not in df.columns:
            print("数据缺少必要字段（需要：价格、成交量、溢价率）")
            return

        conditions = (
            (df[price_col] >= 100) &
            (df[price_col] <= 120) &
            (df[vol_col] >= 40000) &
            (df[premium_col] < 20)
        )

        candidates = df[conditions].copy()
        candidates = candidates.sort_values(vol_col, ascending=False)

        print("\n筛选条件: 价格100-120, 成交量>40000, 溢价率<20%")
        print(f"符合条件可转债: {len(candidates)} 只")

        code_col = None
        for col in ["bond_code", "代码", "code"]:
            if col in df.columns:
                code_col = col
                break

        name_col = None
        for col in ["bond_name", "名称", "name"]:
            if col in df.columns:
                name_col = col
                break

        display_cols = [c for c in [code_col, name_col, price_col, vol_col, premium_col, change_col] if c and c in candidates.columns]

        if not candidates.empty:
            print(candidates[display_cols].head(10).to_string(index=False))
        else:
            print("暂无符合条件的可转债")

    except Exception as e:
        print(f"筛选失败: {e}")


if __name__ == "__main__":
    example_basic()
    example_top_movers()
    example_active_bonds()
    example_price_range()
    example_find_bond()
    example_comprehensive_filter()