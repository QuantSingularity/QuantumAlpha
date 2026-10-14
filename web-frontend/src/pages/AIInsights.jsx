import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Grid,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  useGenerateAiSignalsMutation,
  useGetAiModelHealthQuery,
  useGetAiModelsQuery,
  useGetAiPredictionMutation,
} from "../services/api";
import { palette } from "../theme/tokens";

const STRATEGIES = ["prediction", "technical", "ensemble"];

const errorMessage = (error) =>
  error?.data?.error?.message ||
  error?.data?.error ||
  error?.error ||
  "Request failed";

const signalColor = (type) =>
  type === "buy"
    ? palette.mint
    : type === "sell"
      ? palette.rose
      : palette.textDim;

const percent = (value) =>
  `${value >= 0 ? "+" : ""}${(Number(value) * 100).toFixed(2)}%`;

const AIInsights = () => {
  const { data: models = [], isLoading: modelsLoading } = useGetAiModelsQuery();
  const [generateSignals, signalState] = useGenerateAiSignalsMutation();
  const [predict, predictState] = useGetAiPredictionMutation();
  const [symbolsText, setSymbolsText] = useState("AAPL, MSFT");
  const [strategy, setStrategy] = useState("technical");
  const [selectedModel, setSelectedModel] = useState("");
  const [signals, setSignals] = useState([]);
  const [failures, setFailures] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [formError, setFormError] = useState(null);

  const trained = useMemo(
    () =>
      (Array.isArray(models) ? models : []).filter(
        (m) => m.status === "trained",
      ),
    [models],
  );
  const modelId = selectedModel || trained[0]?.id || "";
  const symbols = useMemo(
    () =>
      symbolsText
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean)
        .slice(0, 20),
    [symbolsText],
  );
  const primarySymbol = symbols[0];
  const { data: health } = useGetAiModelHealthQuery(
    { modelId, symbol: primarySymbol },
    { skip: !modelId || !primarySymbol },
  );

  const needsModel = strategy !== "technical";

  const run = async () => {
    setFormError(null);
    if (!symbols.length) {
      setFormError("Enter at least one symbol");
      return;
    }
    if (needsModel && !modelId) {
      setFormError("Train a model first to use this strategy");
      return;
    }
    try {
      const body = { symbols, strategy };
      if (modelId) body.model_id = modelId;
      const result = await generateSignals(body).unwrap();
      setSignals(result.signals || []);
      setFailures(result.errors || []);
      if (modelId) {
        try {
          setForecast(
            await predict({
              model_id: modelId,
              symbol: primarySymbol,
            }).unwrap(),
          );
        } catch (error) {
          setForecast(null);
        }
      }
    } catch (error) {
      setFormError(errorMessage(error));
    }
  };

  const chartData = useMemo(() => {
    if (!forecast) return [];
    return [
      {
        label: "Now",
        value: forecast.latest_price,
        band: [forecast.latest_price, forecast.latest_price],
      },
      ...forecast.predictions.map((p) => ({
        label: `+${p.step}`,
        value: p.value,
        band: [p.lower, p.upper],
      })),
    ];
  }, [forecast]);

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        AI Insights
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <TextField
                fullWidth
                label="Symbols"
                value={symbolsText}
                onChange={(e) => setSymbolsText(e.target.value)}
                helperText="Comma separated, up to 20"
                sx={{ mb: 2 }}
              />
              <TextField
                select
                fullWidth
                label="Strategy"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                sx={{ mb: 2 }}
              >
                {STRATEGIES.map((item) => (
                  <MenuItem key={item} value={item}>
                    {item}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                select
                fullWidth
                label="Model"
                value={modelId}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={modelsLoading || trained.length === 0}
                helperText={
                  trained.length === 0 ? "No trained models available" : " "
                }
                sx={{ mb: 2 }}
              >
                {trained.map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name} ({model.type})
                  </MenuItem>
                ))}
              </TextField>
              <Button
                fullWidth
                variant="contained"
                onClick={run}
                disabled={signalState.isLoading || predictState.isLoading}
              >
                {signalState.isLoading || predictState.isLoading ? (
                  <CircularProgress size={22} />
                ) : (
                  "Generate Signals"
                )}
              </Button>
              {formError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {formError}
                </Alert>
              )}
              {health && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Model health</Typography>
                  <Chip
                    size="small"
                    color={health.needs_retraining ? "warning" : "success"}
                    label={
                      health.needs_retraining
                        ? "Retraining recommended"
                        : "Healthy"
                    }
                    sx={{ mr: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {Math.round(health.age_days)} days old
                    {health.drift ? `, drift ${health.drift.status}` : ""}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Signals
              </Typography>
              {signals.length === 0 ? (
                <Typography color="text.secondary">
                  Run the generator to see signals.
                </Typography>
              ) : (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Signal</TableCell>
                      <TableCell align="right">Strength</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell align="right">Expected return</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {signals.map((signal) => (
                      <TableRow key={`${signal.symbol}-${signal.strategy}`}>
                        <TableCell>{signal.symbol}</TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={signal.type.toUpperCase()}
                            sx={{
                              color: "#fff",
                              backgroundColor: signalColor(signal.type),
                            }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          {(signal.strength * 100).toFixed(0)}%
                        </TableCell>
                        <TableCell align="right">
                          ${Number(signal.price).toFixed(2)}
                        </TableCell>
                        <TableCell align="right">
                          {signal.prediction
                            ? percent(signal.prediction.expected_return)
                            : "n/a"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              {failures.map((item) => (
                <Alert key={item.symbol} severity="warning" sx={{ mt: 1 }}>
                  {item.symbol}: {item.error}
                </Alert>
              ))}
            </CardContent>
          </Card>
          {forecast && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {forecast.symbol} forecast
                </Typography>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  {forecast.prediction.direction}, probability of a rise{" "}
                  {(forecast.prediction.probability_up * 100).toFixed(0)}%
                </Typography>
                <Box sx={{ height: 280 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="label" />
                      <YAxis domain={["auto", "auto"]} />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="band"
                        stroke="none"
                        fill={palette.violet}
                        fillOpacity={0.15}
                      />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke={palette.mint}
                        fill="none"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default AIInsights;
