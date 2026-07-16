import { budgetStatus, formatClock, type BudgetStatus } from "../session";

export interface TimerInfo {
  totalElapsedS: number;
  totalLimitMin: number;
  part: number;
  partElapsedS: number;
  partBudgetMin: number;
}

const COLORS: Record<BudgetStatus, string> = {
  ok: "text-gray-300",
  amber: "text-amber-400",
  red: "text-red-400 font-semibold",
};

export function TimerBar({ info }: { info: TimerInfo }) {
  const totalStatus = budgetStatus(info.totalElapsedS, info.totalLimitMin);
  const partStatus = budgetStatus(info.partElapsedS, info.partBudgetMin);
  return (
    <span className="font-mono text-sm" title="Pressure, not enforcement">
      <span className={COLORS[totalStatus]}>
        {formatClock(info.totalElapsedS)} / {formatClock(info.totalLimitMin * 60)}
      </span>
      <span className="text-gray-600"> · </span>
      <span className={COLORS[partStatus]}>
        Part {info.part}: {formatClock(info.partElapsedS)} / {formatClock(info.partBudgetMin * 60)}
      </span>
    </span>
  );
}
