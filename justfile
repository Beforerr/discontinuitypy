env-update:
  #!/usr/bin/env sh
  mamba env update --file environment.yml

env-create:
  mamba env create --file environment.yml --force
  # conda activate $(CONDA_ENV)
  # pip install -e .

kedro-run-mag-feature mission:
  kedro run --to-outputs={{mission}}.MAG.feature_ts_1s_tau_60s --from-inputs={{mission}}.MAG.primary_data_ts_1s


kedro-run-candidates:
  kedro run --to-outputs=events.STA_ts_1s_tau_60s --from-inputs=STA.MAG.feature_ts_1s_tau_60s

kedro-run-primary_states:
  kedro run --to-outputs=sta.primary_state_1h 
  kedro run --to-outputs=jno.primary_state_1h
  kedro run --to-outputs=thb.primary_state_1h


kedro-run-sw-events:
  # kedro run --to-outputs=events.sw.thb_ts_1s_tau_60s --from-inputs=candidates.thb_ts_1s_tau_60s
  kedro run --to-outputs=events.l1.ALL_sw_ts_1s_tau_60s --from-inputs=JNO.MAG.feature_ts_1s_tau_60s,STA.MAG.feature_ts_1s_tau_60s,THB.MAG.feature_ts_1s_tau_60s,Wind.MAG.feature_ts_1s_tau_60s
  kedro run --to-outputs=events.l1.ALL_sw_ts_1s_tau_60s --from-inputs=events.JNO_ts_1s_tau_60s,events.Wind_ts_1s_tau_60s,events.THB_sw_ts_1s_tau_60s,events.STA_ts_1s_tau_60s

create-mission-notebooks mission:
  mkdir -p notebooks/missions/{{mission}}
  kedro pipeline create {{mission}}
  touch notebooks/missions/{{mission}}/index.ipynb
  touch notebooks/missions/{{mission}}/mag.ipynb
  touch notebooks/missions/{{mission}}/state.ipynb