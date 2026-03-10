import duckdb
import json

con = duckdb.connect('data/frc2026.duckdb', read_only=True)
q = '''
SELECT
  SUM(CASE WHEN COALESCE(blue_g206_penalty,0) <> 0 THEN 1 ELSE 0 END) AS blue_matches_with_g206,
  SUM(COALESCE(blue_g206_penalty,0)) AS blue_g206_total_points,
  SUM(CASE WHEN COALESCE(red_g206_penalty,0) <> 0 THEN 1 ELSE 0 END) AS red_matches_with_g206,
  SUM(COALESCE(red_g206_penalty,0)) AS red_g206_total_points
FROM tba.matches;
'''
res = con.execute(q).fetchone()
summary = {
    'blue_matches_with_g206': int(res[0]) if res[0] is not None else 0,
    'blue_g206_total_points': int(res[1]) if res[1] is not None else 0,
    'red_matches_with_g206': int(res[2]) if res[2] is not None else 0,
    'red_g206_total_points': int(res[3]) if res[3] is not None else 0,
}
print(json.dumps({'summary': summary}))

rows = con.execute("SELECT key, event_key, comp_level, match_number, red_score, blue_score, red_g206_penalty, blue_g206_penalty FROM tba.matches WHERE COALESCE(red_g206_penalty,0)<>0 OR COALESCE(blue_g206_penalty,0)<>0 ORDER BY match_number LIMIT 20").fetchall()
print(json.dumps({'sample_matches': [list(r) for r in rows]}))
