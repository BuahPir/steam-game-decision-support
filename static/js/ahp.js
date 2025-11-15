// Daftar kriteria tetap (sesuai dengan HTML yang dimodifikasi)
const criteria = [
    'Price', 
    'Recommendations Total', 
    'Release Year', 
    'Min RAM', 
    'CPU Min', 
    'GPU Min',
    'Steam Rating Label', 
    'Steam Chart Player 30d Avg', 
    'Steam Chart Current Player'
];

let weights = [];

// Helper function untuk membuat radio button
function createRadio(name, value, text, isChecked = false) {
    const radioId = `radio_${name}_${value.toString().replace('.', '_')}`;
    let checkedAttr = isChecked ? 'checked' : '';
    let labelClass = value === 1 ? 'center-label' : '';
    
    return `
        <div>
            <input type="radio" id="${radioId}" name="${name}" value="${value}" ${checkedAttr}>
            <label for="${radioId}" class="${labelClass}">
                <span>${text}</span>
            </label>
        </div>
    `;
}

// Fungsi untuk generate tabel perbandingan
function generatePairwiseComparisons() {
    // Validasi keamanan, meskipun dengan hardcode ini pasti > 2
    if (criteria.length < 2) {
        alert('Please add at least 2 criteria');
        return;
    }
    
    const n = criteria.length;
    const container = document.getElementById('pairwiseComparisonsContainer');
    container.innerHTML = ''; 

    let html = '';
    
    // Loop membuat perbandingan setiap pasangan kriteria
    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            const name = `compare_${i}_${j}`;
            html += `
                <div class="comparison-row">
                    <div class="comparison-row-header">
                        <strong class="compare-label-left">${criteria[i]}</strong>
                        <strong class="compare-label-right">${criteria[j]}</strong>
                    </div>
                    <div class="radio-scale">
                        ${createRadio(name, 9, '9')}
                        ${createRadio(name, 8, '8')}
                        ${createRadio(name, 7, '7')}
                        ${createRadio(name, 6, '6')}
                        ${createRadio(name, 5, '5')}
                        ${createRadio(name, 4, '4')}
                        ${createRadio(name, 3, '3')}
                        ${createRadio(name, 2, '2')}
                        ${createRadio(name, 1, '1', true)}
                        ${createRadio(name, 1/2, '2')}
                        ${createRadio(name, 1/3, '3')}
                        ${createRadio(name, 1/4, '4')}
                        ${createRadio(name, 1/5, '5')}
                        ${createRadio(name, 1/6, '6')}
                        ${createRadio(name, 1/7, '7')}
                        ${createRadio(name, 1/8, '8')}
                        ${createRadio(name, 1/9, '9')}
                    </div>
                </div>
            `;
        }
    }
    
    container.innerHTML = html;
    document.getElementById('pairwiseSection').style.display = 'block';
}

// Mengambil nilai dari input radio button menjadi matriks
function getPairwiseMatrix() {
    const n = criteria.length;
    const matrix = Array.from({ length: n }, () => Array(n).fill(1));
    
    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            const name = `compare_${i}_${j}`;
            const checkedRadio = document.querySelector(`input[name="${name}"]:checked`);
            if (checkedRadio) {
                const value = parseFloat(checkedRadio.value);
                matrix[i][j] = value;
                matrix[j][i] = 1 / value;
            }
        }
    }
    return matrix;
}

// Mengirim data ke Python (Flask) untuk perhitungan
async function calculateWeights() {
    const matrix = getPairwiseMatrix();
    
    try {
        const response = await fetch('/calculate_ahp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                criteria: criteria,
                pairwise_matrix: matrix
            })
        });
        
        const data = await response.json();
        
        if (data.success === true) {
            weights = data.weights;
            displayResults(data);
        } else if (data.success === false) {
            alert('Error: ' + data.error);
        } else {
            alert('Unexpected response format');
        }
    } catch (error) {
        alert('Error calculating weights: ' + error);
    }
}

// Menampilkan hasil perhitungan
function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    
    let html = '<h3>Criteria Weights</h3>';
    
    data.criteria.forEach((criterion, index) => {
        const weight = (data.weights[index] * 100).toFixed(2);
        html += `
            <div class="weight-item">
                <strong>${criterion}</strong>
                <span>${weight}%</span>
            </div>
        `;
    });
    
    const crClass = data.is_consistent ? 'good' : 'bad';
    const crMessage = data.is_consistent 
        ? 'Matrix is consistent (CR < 0.1)' 
        : 'Matrix is inconsistent (CR >= 0.1). Please review your comparisons.';
    
    html += `
        <div class="consistency ${crClass}">
            Consistency Ratio: ${data.consistency_ratio.toFixed(4)}<br>
            ${crMessage}
        </div>
    `;
    
    if (data.is_consistent) {
        // Simpan bobot ke LocalStorage agar bisa dipakai di halaman selanjutnya (SAW)
        localStorage.setItem('ahp_weights', JSON.stringify(data.weights));
        localStorage.setItem('ahp_criteria', JSON.stringify(data.criteria));
        
        html += `
            <a href="/saw" class="next-btn">Next: SAW Ranking</a>
        `;
    }
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}