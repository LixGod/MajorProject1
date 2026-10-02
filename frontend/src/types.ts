export interface ApproachStateData {
  queue_length: number;
  raw_count: number;
  downstream_queue: number;
  wait_since_green_sec: number;
  pressure: number;
  feed_healthy: boolean;
  is_emergency: boolean;
  category_counts: Record<string, number>;
}

export interface PhaseData {
  id: number;
  name: string;
  movements: string[];
}

export interface JunctionTelemetry {
  timestamp: number;
  iso_time: string;
  junction_id: string;
  junction_name: string;
  current_phase: PhaseData;
  signal_state: 'GREEN' | 'ALL_RED_CLEARANCE' | 'RED';
  in_all_red_clearance: boolean;
  remaining_green_sec: number;
  total_green_sec: number;
  approach_states: Record<string, ApproachStateData>;
  alerts: {
    preemption_active: boolean;
    preemption_approach: string | null;
    gridlock_warning: boolean;
    manual_override_active: boolean;
  };
  location: {
    junction_id: string;
    name: string;
    latitude: number;
    longitude: number;
    address: string;
    source: string;
  };
}

export interface AnalyticsComparison {
  baseline: {
    mode: string;
    avg_wait_sec: number;
    p95_wait_sec: number;
    throughput_veh_per_hr: number;
    gridlock_triggers: number;
    preemption_response_sec: number;
  };
  max_pressure: {
    mode: string;
    avg_wait_sec: number;
    p95_wait_sec: number;
    throughput_veh_per_hr: number;
    gridlock_triggers: number;
    preemption_response_sec: number;
  };
  improvement: {
    avg_wait_reduction_pct: number;
    p95_wait_reduction_pct: number;
    throughput_increase_pct: number;
  };
}
