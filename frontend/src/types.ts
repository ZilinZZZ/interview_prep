export interface ProblemMeta {
  id: string;
  title: string;
  company: string;
  round: string;
  language: string;
  time_limit_min: number;
  part_budgets_min: number[];
  tags: string[];
  num_parts: number;
}

export interface PartContent {
  statement: string;
  starter: string | null;
  sample_tests: string;
}

export interface TestResult {
  name: string;
  part: number;
  outcome: "passed" | "failed" | "error";
  duration: number;
  trap: string | null;
  message: string | null;
}

export interface RunResponse {
  tests: TestResult[];
  stdout: string;
  stderr: string;
  timed_out: boolean;
  exit_code: number;
}

export interface ClientStats {
  elapsed_total_s: number;
  elapsed_part_s: number;
  run_count: number;
  submit_count: number;
  skipped_parts: number[];
}

export interface RunRequestBody {
  part: number;
  code: string;
  mode: "run" | "submit";
  client_stats: ClientStats;
}
