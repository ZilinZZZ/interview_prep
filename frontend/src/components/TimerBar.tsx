export interface TimerInfo {
  totalElapsedS: number;
  totalLimitMin: number;
  part: number;
  partElapsedS: number;
  partBudgetMin: number;
}

export function TimerBar({ info: _info }: { info: TimerInfo }) {
  return null; // implemented in Task 9
}
