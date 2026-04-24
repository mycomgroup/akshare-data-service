"""运行时探测器 - 实际调用函数获取返回 schema"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import akshare as ak
from datetime import datetime

logger = logging.getLogger("akshare_data")


class RuntimeProber:
    """运行时探测 akshare 函数的返回数据结构"""

    def __init__(
        self,
        max_workers: int = 5,
        rate_limit: float = 0.5,
        timeout: int = 30,
    ):
        self.max_workers = max_workers
        self.rate_limit = rate_limit  # 每次调用间隔（秒）
        self.timeout = timeout
        self.last_call_time = 0

    def probe_function(
        self,
        func_name: str,
        sample_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """探测单个函数"""
        func = getattr(ak, func_name, None)
        if not func:
            logger.warning(f"Function {func_name} not found")
            return None
        
        # 限速
        self._rate_limit()
        
        try:
            # 1. 尝试无参数调用
            df = func()
            logger.info(f"Probed {func_name} (no params)")
            return self._extract_schema(func_name, df, "no_params")
        except TypeError:
            # 2. 需要参数，使用示例参数
            if not sample_params:
                sample_params = self._get_sample_params(func_name)
            
            if not sample_params:
                logger.warning(f"No sample params for {func_name}")
                return None
            
            try:
                df = func(**sample_params)
                logger.info(f"Probed {func_name} (with params)")
                return self._extract_schema(func_name, df, "with_params")
            except Exception as e:
                logger.error(f"Failed to probe {func_name} with params: {e}")
                return None
        except Exception as e:
            logger.error(f"Failed to probe {func_name}: {e}")
            return None

    def probe_batch(
        self,
        func_names: List[str],
        sample_params_map: Optional[Dict[str, Dict]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """批量探测函数"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.probe_function,
                    name,
                    sample_params_map.get(name) if sample_params_map else None,
                ): name
                for name in func_names
            }
            
            for future in as_completed(futures):
                func_name = futures[future]
                try:
                    result = future.result(timeout=self.timeout)
                    if result:
                        results[func_name] = result
                except Exception as e:
                    logger.error(f"Timeout probing {func_name}: {e}")
        
        logger.info(f"Probed {len(results)}/{len(func_names)} functions")
        return results

    def _extract_schema(
        self,
        func_name: str,
        df: pd.DataFrame,
        probe_type: str,
    ) -> Dict[str, Any]:
        """从 DataFrame 提取 schema"""
        columns = []
        
        for col in df.columns:
            dtype = df[col].dtype
            sample_values = df[col].dropna().head(3).tolist()
            null_rate = df[col].isna().sum() / len(df) if len(df) > 0 else 0
            
            columns.append({
                "name": col,
                "type": self._infer_column_type(dtype),
                "pandas_type": str(dtype),
                "sample_values": sample_values,
                "null_rate": round(null_rate, 3),
                "row_count": len(df),
            })
        
        return {
            "func_name": func_name,
            "probe_type": probe_type,
            "probed_at": datetime.now().isoformat(),
            "columns": columns,
            "shape": df.shape,
        }

    def _infer_column_type(self, dtype: Any) -> str:
        """推断列的数据类型"""
        dtype_str = str(dtype).lower()
        
        if "int" in dtype_str:
            return "int"
        elif "float" in dtype_str:
            return "float"
        elif "datetime" in dtype_str or "date" in dtype_str:
            return "datetime"
        elif "bool" in dtype_str:
            return "bool"
        elif "object" in dtype_str or "string" in dtype_str:
            return "str"
        else:
            return "str"

    def _get_sample_params(self, func_name: str) -> Optional[Dict[str, Any]]:
        """获取示例参数"""
        # 常用示例参数
        sample_params_map = {
            "symbol": "000001",
            "code": "000001",
            "stock": "000001",
            "start_date": "20240101",
            "end_date": "20241231",
            "period": "daily",
            "adjust": "",
            "market": "sh",
        }
        
        # 根据函数名推断参数
        if "stock" in func_name.lower():
            return {"symbol": "000001", "start_date": "20240101", "end_date": "20241231"}
        elif "fund" in func_name.lower() or "etf" in func_name.lower():
            return {"symbol": "510050"}
        elif "bond" in func_name.lower():
            return {"symbol": "113001"}
        elif "index" in func_name.lower():
            return {"symbol": "000001"}
        else:
            return None

    def _rate_limit(self):
        """限速控制"""
        now = time.time()
        elapsed = now - self.last_call_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_call_time = time.time()


if __name__ == "__main__":
    prober = RuntimeProber(max_workers=3, rate_limit=1.0)
    
    # 探测无参数函数
    result1 = prober.probe_function("stock_zh_a_spot_em")
    print(f"stock_zh_a_spot_em: {result1['columns'][:3] if result1 else 'failed'}")
    
    # 探测有参数函数
    result2 = prober.probe_function("stock_zh_a_hist", {"symbol": "000001", "period": "daily"})
    print(f"stock_zh_a_hist: {result2['columns'][:3] if result2 else 'failed'}")