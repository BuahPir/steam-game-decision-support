## Decision Support System for Selecting Steam Games Using a Combination of AHP and SAW Models
<p style="text-align: justify">Proyek ini bertujuan untuk membangun sistem pendukung keputusan (Decision Support System / DSS) yang membantu pengguna dalam menentukan game terbaik di platform Steam berdasarkan preferensi dan kriteria tertentu. Dalam proyek ini digunakan kombinasi dua metode pengambilan keputusan multikriteria, yaitu Analytical Hierarchy Process (AHP) dan Simple Additive Weighting (SAW).</p>

<p style="text-align: justify">Metode AHP digunakan untuk menentukan bobot kepentingan setiap kriteria, seperti harga, genre, rating pengguna, spesifikasi minimum, dan popularitas. Proses ini melibatkan perbandingan berpasangan antar kriteria untuk memperoleh bobot yang objektif dan konsisten. Selanjutnya, metode SAW digunakan untuk melakukan perangkingan alternatif game berdasarkan nilai preferensi yang dihitung dari hasil pembobotan AHP.</p>

<p style="text-align: justify">Sistem ini diimplementasikan dalam bentuk aplikasi berbasis web yang memungkinkan pengguna memasukkan preferensi mereka, melihat perbandingan antar game, serta mendapatkan rekomendasi game yang paling sesuai dengan kebutuhan mereka. Dengan kombinasi AHP dan SAW, sistem dapat memberikan hasil yang lebih akurat, terukur, dan transparan dibandingkan dengan rekomendasi subjektif semata.</p>

## INSTALASI
Buat Virtual Environment Python ([pip](https://pip.pypa.io/en/stable/)) sesudah melakukan Clone Repository.
```bash
python -m venv [name_virtual_environment]
```
Setelah Virtual Environment terbuat, Aktifkan Environment untuk download library dan menjalankan app.
```bash
[name_virtual_environment]/Scripts/activate
```
Download library yang sudah berada di ```requirements.txt```
```bash
pip install -r requirements.txt
```
## PENGGUNAAN
Jalankan ```app.py```
```bash
python app.py
```
## LICENSE
The MIT License (MIT)

Copyright (c) 2024 BuahPir

<p style="text-align: justify">Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

<p style="text-align: justify">The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

<p style="text-align: justify">THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</p>