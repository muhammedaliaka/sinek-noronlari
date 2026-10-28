# Bu depoda çalışırken

Proje: sinek beyni esinli "dijital canlı" (koku/ödül öğrenme, bellek, karar). Yol haritası: `README.md`, `docs/proje_raporu.md`. Dil: Türkçe, dürüst raporlama.

1. **Karar vermeden önce** `docs/karar_defteri.md` içindeki "Değişmez kurallar" ve "Hata sicili" bölümlerini oku; **karardan/hatadan sonra** oraya kayıt ekle.
2. Doğrulayıcı koşular, ön-kayıt belgesi (`docs/evre*_plan.md`) commit edilmeden başlamaz; ölçütler koşudan sonra değişmez; başarısızlık raporlanır.
3. Yeni ölçüt/karar kuralı kullanılmadan önce sıfır-etki ve bilinen-etki benzetimiyle sınanır (`python -m sinek.experiments.power2b`).
4. Dış kaynaktan gelen rakamlar [doğrulandı]/[doğrulanmadı] etiketlenir. Nöron sayısı bir başarı ölçütü değildir.
5. Büyütme/birleştirme işleri için `docs/birlestirme_risk_analizi.md` (riskler, yedek planlar, kapılar) esastır.
6. Komutlar: testler `python3 -I -m pytest -q tests`; koşular `python3 -I -m sinek.experiments.<modül>` (sonuçlar `results/`, git'te yok).
