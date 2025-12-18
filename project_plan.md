MLB-Game-Schedule-Analyzer - Project Plan (v1.0)
==========================================

DESCRIPTION
-----------
Analyzes a full MLB season schedule to identify the most valuable games 
for each team based on tiebreaker implications and standings impact.


FEATURES
--------

1. Team Selection
   - Selectbox dropdown with all 30 MLB teams
   - Shows team logo when selected along with team name in selectbox

2. Schedule Data
   - Pull full MLB schedule via MLB Stats API
   - Pull all MLB team Logos

     Data Storage Strategy:
     - Supabase: MLB logos (cache 1 day), full schedule (cache 1 hour).

     Calculate on the fly:
     - Game Value — fast math on 162 games, milliseconds
   

3. Visual Schedule Display
   - Calendar/grid view of full season schedule
   - 2x3 or 3x2 month grid layout
     * March/April (combined) | May | June
     * July | August | September
   - Scales based on screen size/orientation
   - Show the team names and logos on schedule
   - Color-coded games by importance level
   - Color key/legend explaining the scale

4. Hover Tooltips
   - Hover over any game to see:
     * Why it's rated that importance level
     * Which tiebreaker(s) it affects

5. Tiebreaker Reference Panel
   - Sidebar showing the tiebreaker rules hierarchy


TIEBREAKER RULES (Two-Team Ties)
--------------------------------
1. Head-to-head record
   - Season series between the tied teams decides it
   - Example: Team X goes 10-8 vs Team Y → Team X wins tiebreaker

2. Intradivision record
   - If head-to-head is tied, compare records within division
   - Applies even for Wild Card ties between teams in different divisions
   - Example: Yankees and Red Sox split 9-9, but Yankees went 45-31 vs AL East 
     while Red Sox went 42-34 → Yankees win tiebreaker

3. Intraleague record
   - If still tied, compare records vs all teams in same league
   - AL teams vs AL teams, NL teams vs NL teams
   - Example: Dodgers and Padres tied in head-to-head and division record,
     but Dodgers went 60-46 vs NL while Padres went 58-48 → Dodgers win tiebreaker

4. Last half of intraleague games
   - Records from intraleague games after the All-Star break
   - Not the exact mathematical midpoint
   - Example: Two teams tied through tiebreakers 1-3, but Team A went 30-20 
     in second-half intraleague games vs Team B's 28-22 → Team A wins tiebreaker

5. Last half plus one intraleague game
   - Work backwards from last intraleague game until tie is broken
   - Example: Still tied after tiebreaker 4, look at the last intraleague game 
     of the first half. 
     
     Did Team A or Team B win that game? Winner takes tiebreaker.
     If that game was also a tie (or wasn't between these teams), go back one more 
     intraleague game. Keep going backwards until the tie is resolved.


GAME VALUE CALCULATION
----------------------
Each game scored 0-100 based on tiebreaker impact.

FACTORS TO CONSIDER (scoring TBD):
   - Division vs Intraleague vs Interleague
   - Second half of season (after All-Star break)
   - Late September timing (for final tiebreak)

SCORE RANGES & COLORS (gradient):
   90-100: Critical       (Dark Red)
   70-89:  Very Important (Red)
   50-69:  Important      (Orange)
   30-49:  Moderate       (Yellow)
   10-29:  Low            (Light Green)
   0-9:    Minimal        (Light Blue)

COLOR DISPLAY:
   - Small colored circle in corner of each game slot
   - Keeps game info readable
   - Doesn't overwhelm the schedule view

TODO: Figure out statistical approach for weighting tie breaker factors listed above


TECH STACK
----------
- Python
- Streamlit
- Supabase (PostgreSQL)
- MLB Stats API (statsapi library)
- Pandas
- Render (deployment)


STRETCH GOALS (v1.5)
------------------

Colorblind Mode:
   - Alternative color palette for colorblind users
   - Toggle option in settings


STRETCH GOALS (v2.0)
------------------
- Dynamic updates throughout season (re-calculate after each game)
- Factor in which teams are actual contenders based on standings
- "Games that mattered most" retrospective after season ends