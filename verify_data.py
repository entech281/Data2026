import duckdb
conn = duckdb.connect('data/frc2026.duckdb')

print("=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)

print("\n✓ Teams synced:")
teams = conn.execute("SELECT COUNT(*) as count FROM frc_teams").fetchone()
print(f"  {teams[0]} teams total")

print("\n✓ Matches synced:")
matches = conn.execute("SELECT COUNT(*) as count FROM event_match").fetchone()
print(f"  {matches[0]} matches total")

print("\n✓ OPRs synced:")
oprs = conn.execute("SELECT COUNT(*) as count FROM calculated_data").fetchone()
print(f"  {oprs[0]} team-event records with OPR/DPR/CCWM")

print("\n" + "=" * 60)
print("Sample Data:")
print("=" * 60)

print("\nTeams (first 5):")
for row in conn.execute("SELECT * FROM frc_teams LIMIT 5").fetchall():
    print(f"  Team {row[0]}: {row[1]}")

print("\nMatches (first 3):")
for row in conn.execute("SELECT match_id, event_id, match_type, match_number, red_1, red_2, red_3, red_total_points FROM event_match LIMIT 3").fetchall():
    print(f"  Match {row[3]} ({row[2]}): Red alliance ({row[4]},{row[5]},{row[6]}) - {row[7]} points")

print("\nOPRs (first 5):")
for row in conn.execute("SELECT team_number, event_id, event_opr, event_dpr, event_ccwm FROM calculated_data LIMIT 5").fetchall():
    print(f"  Team {row[0]}: OPR={row[2]:.1f}, DPR={row[3]:.1f}, CCWM={row[4]:.1f}")
