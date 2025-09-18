from flask import Flask, jsonify
from scraper import get_antecedentes
import asyncio

app = Flask(__name__)

@app.route('/antecedentes/<cedula>', methods=['GET'])
def antecedentes(cedula):
    result = asyncio.run(get_antecedentes(cedula))
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
