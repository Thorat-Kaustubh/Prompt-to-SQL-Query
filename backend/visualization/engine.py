import datetime
import re
from typing import List, Dict, Any, Optional

class VisualizationEngine:
    """
    VISUALIZATION ENGINE (visualization/) - Senior Data Visualization Engineer
    - Analyzes query results and detects patterns.
    - Generates BI-grade chart configurations (Chart.js/Recharts/ECharts compatible).
    - Auditor-Fixes applied: KPI Groups, Advanced Date Detection, Cardinality Guards.
    """

    def __init__(self):
        pass

    def analyze_and_configure(self, data: List[Dict[str, Any]], execution_ms: float = 0.0) -> Dict[str, Any]:
        """
        Main entry point for generating visualization configuration.
        Returns both raw table data and the chart config.
        """
        if not data:
            return {
                "table": [],
                "chart": None,
                "summary": "No data found.",
                "metadata": {"execution_ms": execution_ms, "status": "empty"}
            }

        # 1. Inspect structure
        columns = list(data[0].keys())
        num_rows = len(data)

        # 2. Pattern detection
        chart_type = self._detect_pattern(data, columns)
        
        # 3. Handle Cardinality (Top N + Others)
        processed_data = data
        if chart_type in ["bar", "pie", "grouped_bar"] and num_rows > 15:
            # Detect primary numeric and categorical columns for sorting
            numeric_cols = [c for c in columns if isinstance(data[0].get(c), (int, float))]
            categorical_cols = [c for c in columns if c not in numeric_cols and not self._is_date_column(c, data[0].get(c))]
            
            if numeric_cols and categorical_cols:
                processed_data = self._apply_cardinality_limit(data, categorical_cols[0], numeric_cols[0], limit=15)

        # 4. Generate configuration
        chart_config = self._generate_config(processed_data, columns, chart_type)

        # 5. Generate Insight
        insight = self._generate_insight(processed_data, columns, chart_type)

        return {
            "table": data, # Return FULL table data regardless of chart limits
            "chart": chart_config,
            "summary": insight,
            "metadata": {
                "execution_ms": execution_ms,
                "rows": num_rows,
                "shown_rows": len(processed_data),
                "columns": columns,
                "detected_type": chart_type
            }
        }

    def _apply_cardinality_limit(self, data: List[Dict[str, Any]], label_col: str, value_col: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        High Priority Fix: Prevents UI bloat by grouping low-value items into 'Others'.
        """
        if len(data) <= limit: return data
        
        # Sort by the primary value column descending
        sorted_data = sorted(data, key=lambda x: x.get(value_col, 0) or 0, reverse=True)
        top_n = sorted_data[:limit-1]
        others = sorted_data[limit-1:]
        
        # Aggregate others into a single row
        others_row = {label_col: "Others (Total)"}
        for col in sorted_data[0].keys():
            if col == label_col: continue
            
            # Sum numeric values
            vals = [row.get(col, 0) for row in others if isinstance(row.get(col), (int, float))]
            if vals:
                others_row[col] = round(sum(vals), 2)
            else:
                others_row[col] = "..." # Placeholder for non-numeric data in others
                
        return top_n + [others_row]

    def _generate_insight(self, data: List[Dict[str, Any]], columns: List[str], chart_type: str) -> str:
        """
        Generates a human-readable summary/insight from the data.
        Refactored for better business context.
        """
        if not data: return "No data found."
        
        try:
            numeric_cols = [col for col in columns if isinstance(data[0].get(col), (int, float))]
            categorical_cols = [col for col in columns if col not in numeric_cols and not self._is_date_column(col, data[0].get(col))]
            
            if chart_type == "kpi":
                col = columns[0]
                return f"Total {col.replace('_', ' ').title()}: {self._format_value(data[0][col])}."
            
            if chart_type == "kpi_group":
                metrics = [f"{c.replace('_', ' ').title()} ({self._format_value(data[0][c])})" for c in numeric_cols[:3]]
                return f"Key Performance Indicators: {', '.join(metrics)}."

            if chart_type in ["bar", "pie"] and categorical_cols and numeric_cols:
                x, y = categorical_cols[0], numeric_cols[0]
                # Filter out "Others" for the peak insight
                real_data = [r for r in data if r[x] != "Others (Total)"]
                if real_data:
                    max_row = max(real_data, key=lambda r: r.get(y, 0))
                    return f"'{max_row[x]}' leads with {self._format_value(max_row[y])} {y.replace('_', ' ')}."
            
            if chart_type == "line" and numeric_cols:
                y = numeric_cols[0]
                if len(data) >= 2:
                    first = data[0].get(y, 0)
                    last = data[-1].get(y, 0)
                    diff_pct = ((last - first) / first * 100) if first != 0 else 0
                    trend = "increased" if last > first else "decreased"
                    return f"{y.replace('_', ' ').title()} {trend} by {abs(diff_pct):.1f}% over the analyzed period."
                    
        except Exception: pass
        return "Data retrieved successfully."

    def _format_value(self, val: Any) -> str:
        """
        Medium Fix: Scales large numbers for better readability (1.2M, 45K).
        """
        if not isinstance(val, (int, float)): return str(val)
        abs_v = abs(val)
        if abs_v >= 1_000_000: return f"{val/1_000_000:.1f}M"
        if abs_v >= 1_000: return f"{val/1_000:.1f}K"
        if isinstance(val, float): return f"{val:.2f}"
        return f"{val:,}" # Comma separated

    def _detect_pattern(self, data: List[Dict[str, Any]], columns: List[str]) -> str:
        """
        Critical Fixes: KPI Groups and Axis Validation.
        """
        num_rows = len(data)
        numeric_cols = [col for col in columns if isinstance(data[0].get(col), (int, float))]
        date_cols = [col for col in columns if self._is_date_column(col, data[0].get(col))]
        categorical_cols = [col for col in columns if col not in numeric_cols and col not in date_cols]

        # 1. Single Row (KPI or KPI Group)
        if num_rows == 1:
            if len(numeric_cols) == 1: return "kpi"
            if len(numeric_cols) > 1: return "kpi_group"
            return "table"

        # 2. Time Series
        if date_cols and len(data) > 1 and numeric_cols:
            return "line"

        # 3. Categorical / Distribution
        if categorical_cols and numeric_cols:
            if len(categorical_cols) == 1 and len(numeric_cols) == 1:
                # Use pie for very small distributions
                if 2 <= num_rows <= 8: return "pie"
                return "bar"
            return "grouped_bar"

        # 4. Fallback: Security Check
        # If no categorical labels exist, don't force a Bar Chart with numeric X-Axis
        return "table"

    def _is_date_column(self, col_name: str, value: Any) -> bool:
        """
        High Priority Fix: expanded date detection for diverse SQL formats.
        """
        name_keywords = ['date', 'time', 'timestamp', 'created_at', 'updated_at', 'month', 'year', 'day', 'week', 'period', 'dt']
        if any(kw == col_name.lower() or f"{kw}_" in col_name.lower() or f"_{kw}" in col_name.lower() for kw in name_keywords):
            return True
        
        if isinstance(value, (datetime.date, datetime.datetime)): return True
        
        if isinstance(value, str):
            # ISO: 2024-01-01
            if re.match(r'^\d{4}-\d{2}-\d{2}', value): return True
            # DD/MM/YYYY or DD-MM-YYYY
            if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', value): return True
            # Month YYYY: Jan 2024
            if re.match(r'^[A-Za-z]{3,9}\s+\d{2,4}', value): return True
            # ISO-8601 with T
            if 'T' in value and (value.endswith('Z') or '+' in value): return True
        
        return False

    def _generate_config(self, data: List[Dict[str, Any]], columns: List[str], chart_type: str) -> Optional[Dict[str, Any]]:
        """
        Generates Chart.js / Recharts compatible JSON.
        """
        if chart_type == "table": return None

        numeric_cols = [col for col in columns if isinstance(data[0].get(col), (int, float))]
        date_cols = [col for col in columns if self._is_date_column(col, data[0].get(col))]
        categorical_cols = [col for col in columns if col not in numeric_cols and col not in date_cols]

        config = {
            "type": chart_type,
            "title": "Business Intelligence Analysis",
            "labels": [],
            "datasets": [],
            "metadata": {"x_axis": "", "y_axis": []}
        }

        if chart_type == "kpi":
            col = numeric_cols[0]
            config.update({"value": data[0][col], "formatted": self._format_value(data[0][col]), "label": col.upper()})

        elif chart_type == "kpi_group":
            config["metrics"] = []
            for col in numeric_cols:
                config["metrics"].append({"label": col.replace('_', ' ').title(), "value": data[0][col], "formatted": self._format_value(data[0][col])})

        elif chart_type == "line":
            x_axis = date_cols[0] if date_cols else columns[0]
            config["labels"] = [str(row[x_axis]) for row in data]
            config["metadata"]["x_axis"] = x_axis
            for col in numeric_cols:
                config["datasets"].append({"label": col.replace('_', ' ').title(), "data": [row[col] for row in data]})
                config["metadata"]["y_axis"].append(col)

        elif chart_type in ["bar", "grouped_bar", "pie"]:
            x_axis = categorical_cols[0] if categorical_cols else columns[0]
            config["labels"] = [str(row[x_axis]) for row in data]
            config["metadata"]["x_axis"] = x_axis
            for col in numeric_cols:
                config["datasets"].append({"label": col.replace('_', ' ').title(), "data": [row[col] for row in data]})
                config["metadata"]["y_axis"].append(col)

        return config
