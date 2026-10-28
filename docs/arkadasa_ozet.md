# Proje özeti (sade anlatım)

> Son güncelleme: 2026-10-28, ana doğrulayıcı koşular bitti; bir kontrol deneyi (E1) hâlâ sürüyor.

Bu projede gerçek bir meyve sineğinin beyin haritasından yola çıkarak bilgisayarda yaşayan basit bir yapay "yaratık" geliştiriyoruz. Sineğin kokuları öğrenmesini sağlayan
bölgesinin gerçek bağlantı haritasını aldık ve yaratığı sanal bir dünyaya koyduk: iki kokudan hangisinin ödül getirdiğini deneme yanılmayla öğreniyor, ödül diğer kokuya geçince
fikrini değiştiriyor ve öğrendiğini kaydedip sonradan geri yükleyebiliyor. Önce basit, uydurma bir beyinle bunu başardık; gerçek sinek haritasıyla yaptığımız ilk denemede öğrenme görüldü ama ölçüm yöntemimiz yeterince güçlü olmadığı için testlerimizin bir kısmını geçemedik ve bunu saklamadan "başarısız" diye yazdık. Sonra ölçüm yöntemini düzeltip kuralları baştan yazdık ve testi yeni denemelerle tekrarladık: bu sefer iki ayrı denemede de yaratık hem öğrendi hem ödül değişince fikrini değiştirdi ve tüm testlerimizi geçti. Dürüst olmak gerekirse öğrenme orta düzeyde (ödüllü kokuyu yaklaşık yüzde 73 seçiyor, yazı-tura yüzde 50 olurdu) ve "hatasını fark etme" kısmı henüz gerçek beyin bağlantısından değil elle yazılmış bir kuraldan geliyor. Asıl hedefimiz, ileride çok daha büyük bir sinek beyni modeliyle
(yüz binlerce nöron ve kendi tasarlayacağımız ek nöronlarla) önce basit oyunlarda, sonra başka testlerde en hızlı öğrenen ve hatalarından en çabuk ders çıkaran yapay beyni üretmek;
amaç nöron sayısını artırmak değil, gerçekten daha akıllı olanı bulmak. Bunun için güçlü bir ekran kartı gerekecek, o aşamaya henüz geçmedik.
