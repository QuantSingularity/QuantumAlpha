import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  useTheme,
} from "@mui/material";

const StrategyTable = ({ strategies }) => {
  const theme = useTheme();

  return (
    <Box sx={{ overflowX: "auto" }}>
      <TableContainer>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Strategy</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>
                Return (%)
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>
                Sharpe
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>
                Max DD (%)
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 600 }}>
                Action
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {strategies.map((strategy, index) => (
              <TableRow
                key={index}
                sx={{
                  "&:hover": {
                    backgroundColor: "rgba(255, 255, 255, 0.05)",
                  },
                  transition: "background-color 0.2s ease",
                }}
              >
                <TableCell component="th" scope="row" sx={{ fontWeight: 500 }}>
                  {strategy.name}
                </TableCell>
                <TableCell
                  align="right"
                  sx={{
                    color:
                      strategy.return > 0
                        ? theme.palette.primary.main
                        : theme.palette.error.main,
                    fontWeight: 500,
                  }}
                >
                  {strategy.return > 0 ? "+" : ""}
                  {strategy.return}%
                </TableCell>
                <TableCell align="right">{strategy.sharpe}</TableCell>
                <TableCell
                  align="right"
                  sx={{ color: theme.palette.error.main }}
                >
                  {strategy.drawdown}%
                </TableCell>
                <TableCell align="center">
                  <Button
                    size="small"
                    variant="outlined"
                    color="primary"
                    sx={{
                      minWidth: "80px",
                      fontWeight: 500,
                    }}
                  >
                    Details
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default StrategyTable;
