env-update:
  #!/usr/bin/env sh
  mamba env update --file environment.yml

env-create:
  mamba env create --file environment.yml --force
  # conda activate $(CONDA_ENV)
  # pip install -e .

kedro-run-mag:
  kedro run --to-outputs=JNO.MAG.feature_ts_1s_tau_60s --from-inputs=JNO.MAG.primary_data_ts_1s


kedro-run-candidates:
  # kedro run --to-outputs=candidates.sta_tau_60s --from-inputs=sta.feature_tau_60s
  # kedro run --to-outputs=candidates.jno_tau_60s --from-inputs=jno.feature_tau_60s
  # kedro run --to-outputs=candidates.thb_tau_60s --from-inputs=thb.feature_tau_60s
  # kedro run --to-outputs=candidates.thb_ts_1s_tau_60s --from-inputs=thb.feature_ts_1s_tau_60s


kedro-run-primary_states:
  kedro run --to-outputs=sta.primary_state_1h 
  kedro run --to-outputs=jno.primary_state_1h
  kedro run --to-outputs=thb.primary_state_1h


kedro-run-sw-events:
  kedro run --to-outputs=events.sw.thb_ts_1s_tau_60s --from-inputs=candidates.thb_ts_1s_tau_60s

create-mission-notebooks mission:
  mkdir -p notebooks/missions/{{mission}}
  touch notebooks/missions/{{mission}}/index.ipynb
  touch notebooks/missions/{{mission}}/mag.ipynb
  touch notebooks/missions/{{mission}}/state.ipynb