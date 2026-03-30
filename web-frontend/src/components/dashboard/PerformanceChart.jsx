import { useTheme } from "@mui/material/styles";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PerformanceChart = ({ data, height = 300 }) => {
  const theme = useTheme();

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload?.length) {
      return (
        <div
          style={{
            backgroundColor: theme.palette.background.paper,
            padding: "10px",
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: "4px",
            boxShadow: theme.shadows[3],
          }}
        >
          <p style={{ margin: 0, fontWeight: 600 }}>{`${label}`}</p>
          <p
            style={{
              margin: 0,
              color: theme.palette.primary.main,
            }}
          >{`Value: $${payload[0].value.toLocaleString()}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={data}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
        <XAxis
          dataKey="name"
          stroke={theme.palette.text.secondary}
          tick={{ fill: theme.palette.text.secondary }}
        />
        <YAxis
          stroke={theme.palette.text.secondary}
          tick={{ fill: theme.palette.text.secondary }}
          tickFormatter={(value) => `$${value.toLocaleString()}`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ paddingTop: "10px" }} />
        <Line
          type="monotone"
          dataKey="value"
          stroke={theme.palette.primary.main}
          activeDot={{
            r: 8,
            fill: theme.palette.primary.main,
            stroke: theme.palette.background.paper,
          }}
          strokeWidth={2}
          dot={{
            r: 4,
            fill: theme.palette.primary.main,
            stroke: theme.palette.background.paper,
            strokeWidth: 2,
          }}
          name="Portfolio Value"
          animationDuration={1500}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default PerformanceChart;
