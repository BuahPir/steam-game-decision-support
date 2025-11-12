from flask import Flask, render_template, request, jsonify
from ahp_calculation import AHPCalculation
from saw_calculation import SAWCalculation
from steam_data_fetcher import SteamDataFetcher
from benchmark_fetcher import BenchmarkFetcher
import pandas as pd

app = Flask(__name__)

# Default Steam AppIDs for testing
DEFAULT_APPIDS = [
    1245620, 1174180, 1086940, 2246340, 1446780,
    582010, 513710, 2807960, 108600, 105600,
    413150, 460930, 2231380, 1903340, 3527290,
    275850, 1687950, 648800, 252490, 221100
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ahp')
def ahp_page():
    return render_template('ahp.html')

@app.route('/saw')
def saw_page():
    return render_template('saw.html')

@app.route('/calculate_ahp', methods=['POST'])
def calculate_ahp():
    try:
        data = request.json
        criteria = data['criteria']
        pairwise_matrix = data['pairwise_matrix']
        
        # Use AHP calculation module
        ahp = AHPCalculation(criteria, pairwise_matrix)
        result = ahp.calculate()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/upload_saw_data', methods=['POST'])
def upload_saw_data():
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'})
        
        file = request.files['file']
        
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'})
        
        if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            # Read the Excel file into a pandas DataFrame
            df = pd.read_excel(file)
            
            # Check for empty file
            if df.empty:
                return jsonify({'success': False, 'error': 'Excel file is empty'})

            # Extract data based on the required format
            # Column 0: Alternatives
            # Columns 1...n: Criteria values
            alternatives = df.iloc[:, 0].tolist()
            criteria_from_file = df.columns[1:].tolist()
            decision_matrix = df.iloc[:, 1:].values.tolist()
            
            return jsonify({
                'success': True,
                'alternatives': alternatives,
                'criteria_from_file': criteria_from_file,
                'decision_matrix': decision_matrix
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload .xlsx or .xls'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error processing file: {str(e)}'})

@app.route('/calculate_saw', methods=['POST'])
def calculate_saw():
    try:
        data = request.json
        alternatives = data['alternatives']
        criteria = data['criteria']
        weights = data['weights']
        decision_matrix = data['decision_matrix']
        criteria_types = data['criteria_types']
        
        # Use SAW calculation module
        saw = SAWCalculation(alternatives, criteria, weights, decision_matrix, criteria_types)
        result = saw.calculate()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_steam_games', methods=['GET'])
@app.route('/get_steam_games', methods=['GET'])
def get_steam_games():
    """
    API endpoint to fetch, process, and return Steam game data.
    """
    try:
        print("--- Fetching Steam data... ---")
        steam_fetcher = SteamDataFetcher(delay=1.5)
        games = steam_fetcher.fetch_multiple_games(DEFAULT_APPIDS)
        if not games:
            return jsonify({'success': False, 'error': 'No games fetched from Steam.'}), 500
        print(f"--- Fetched {len(games)} games from Steam. ---")

        print("--- Fetching and combining benchmark data... ---")
        bench_fetcher = BenchmarkFetcher()
        
        for game in games:
            cpu_name = game.get('cpu_minimal')
            gpu_name = game.get('gpu_minimal')
            
            # Call the singular methods: get_cpu_mark and get_gpu_g3d_mark
            game['cpu_mark_score'] = bench_fetcher.get_cpu_mark(cpu_name)
            game['gpu_g3d_score'] = bench_fetcher.get_gpu_g3d_mark(gpu_name)

        print("--- Data combination complete. Sending to client. ---")
        return jsonify({'success': True, 'games': games})

    except Exception as e:
        print(f"!!! CRITICAL ERROR in /get_steam_games: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/search_steam_game/<int:appid>', methods=['GET'])
def search_steam_game(appid):
    """
    API endpoint to fetch, process, and return a SINGLE Steam game by AppID.
    """
    try:
        print(f"--- Fetching AppID: {appid}... ---")
        steam_fetcher = SteamDataFetcher()
        
        games = steam_fetcher.fetch_multiple_games([appid])
        
        if not games:
            return jsonify({'success': False, 'error': f'Game with AppID {appid} not found or failed to fetch.'}), 404
        
        game = games[0]
        
        print("--- Fetching benchmark data for single game... ---")
        bench_fetcher = BenchmarkFetcher()
        
        cpu_name = game.get('cpu_minimal')
        gpu_name = game.get('gpu_minimal')
        
        game['cpu_mark_score'] = bench_fetcher.get_cpu_mark(cpu_name)
        game['gpu_g3d_score'] = bench_fetcher.get_gpu_g3d_mark(gpu_name)
        
        print("--- Single game data combination complete. ---")
        return jsonify({'success': True, 'game': game})

    except Exception as e:
        print(f"!!! CRITICAL ERROR in /search_steam_game: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)