Zum anderen Laser [[ZING_4030#Schneiden:_CUT_-_.28.22Rote_Linie.22.29|(Epilog Zing 4030)]]
{{Infobox Gerät
|Foto = Nova35.png
|Hersteller = Thunderlaser / Allplast
|Typ = Nova 35
|Status = gruen
|KlasseE = gruen
}}

== Abmessungen ==

{| class="wikitable"
|-
| Arbeitsbereich ||style="text-align:right"| 900 x 600 mm
| zweite Zeile || || bam&#124;bum
|-
| Tischfläche ||style="text-align:right"| 1000 x 730 mm
|-
| Maximale Höhe über Tisch ||style="text-align:right"| 230 mm
|-
| Maximale Tischlast ||style="text-align:right"| 40 kg&nbsp;&nbsp;
|-
|}

IP-Addresse: 172.22.30.50 oder DNS-Name: nova35.fablab.lan


== Mögliche Materialien ==

Holz Acryl, Pappe, ... Materialstärken bis ca 8mm.
Siehe https://wiki.fablab-nuernberg.de/w/ZING_4030#M.C3.B6gliche_Materialien

== Vorbereitung ==

Der Nova35 Laser ist nur nach Einweisung nutzbar! Nicht fürs OpenLab freigegeben!

* Nova Laser einschalten unten rechts: Der Drehschalter muss oben stehen, die beiden Kippschalter auf 1.
* Lüftungs-Schlauch vom Zing abziehen, und am Verlängerungsstück des Thunderlaser anstecken.
* Aussen-Absaugung einschalten: Ein grosser Drehschalter + 2 kleine Kippschalter
* Roten Reset-Knopf am Laser drücken.
Das Display startet. Erst danach reagiert der Laser auf USB oder Netzwerk.

=== Benötigte Dateien ===

SVG. Und alles was sich in SVG konvertieren lässt. CDR, AI, EPS, ...

=== Empfohlene Software ===

==== VisiCut ====
VisiCut arbeitet als Erweiterung für Inkscape.
Ein VisiCut mit Unterstützung für den Nova35 kann hier heruntergeladen werden:
https://visicut.org/

Einmalig nach dem Start von VisiCut sollte aus dem Menü "Empfohlene Einstellungen herunterladen" aufgerufen werden,
und die Einstellungen für "FabLab Region Nürnberg e.V." geladen werden. Dann sind alle unsere Laser verfügbar.
Bei Windows muss zusätzlich einmal der Menüpunkt "Install Inkscape Plugin" aufgerufen werden.

Die Material-Profile in den sog. empfohlenen Einstellungen sind fast alle falsch. Man hört immer wieder Gerüchte, man solle prinzipiell immer mit 1 mm mehr Materialstärke lasern. Das ist so allgemein natürlich auch falsch. Viele Materialien tauchen als Auswahl auf, obwohl wir sie noch nie ausprobiert haben. Das ist ein Softwarefehler. Viele Materialien haben Einstellung 10 20 100, das sind die Werte, die das Programm sich ausdenkt, wenn nichts hinterlegt ist. Auch ein Softwarefehler. Bei wichtigen Teilen immer vorher einen kleinen Testschnitt machen! Bitte neue Einstellungen prüfen und mit der Tabelle hier im Wiki vergleichen. Stand Mai 2018 wird die untenstehende Tabelle von juergen@fabmail.org gepflegt. Die 'empfohlenen Einstellungen' sind nur mit erhöhtem Aufwand zu verändern und bleiben daher leider ungepflegt. Ideen bitte an juergen@fabmail.org .

Im Menü Lasercutter Verwalten kann beim Thunderlaser umgeschaltet werden zwischen
* Verbindung über Netzwerk: Im VisiCut (oder rdworks) muss dazu die Adresse '''172.22.30.50''' eingestellt sein. Damit kann der Laser aus dem FabLab WLAN (FLN) von jedem Rechner aus angesteuert werden.
* Falls das Netzwerk nicht will: Dateien für USB-Stick (`D:\test.rd`) ,
* Falls weder Netzwerk, noch USB-Kabel wollen: Verbindung über USB-Kabel (Linux: `/dev/ttyUSB0`, Windows: `com4`)<br
/>Die genaue Nummer der COM-Schnittstelle unter Windows muss unter Systemeinstellungen -> Gerätemanager nachgeschaut werden. Dort erscheint der Name 'FTDI'. Falls gar nichts erscheint muss noch ein FTDI-Treiber installiert werden.

==== Inkscape Thunderlaser Extension ====
Das ist eine Alternative zu VisiCut. Das Programm arbeitet ohne die von VisiCut gewohnten Wartezeiten, ist aber viel einfacher gehalten. https://github.com/jnweiger/inkscape-thunderlaser/releases
Als Ausgabe Datei stehen genau die gleichen Möglichkeiten zur Wahl wie bei VisiCut.

==== CorelDraw mit installiertem RDWorks plugin ====
Bedienung siehe https://raw.githubusercontent.com/jnweiger/ruida-laser/master/doc/laser-nova35-rdworks.md


==== Andere Software ====
* Python: https://github.com/jnweiger/ruida-laser
* https://wiki.fablab-nuernberg.de/w/Diskussion:Nova_35

* rd-Format Decoder: https://github.com/kkaempf/ruida

== Durchführung ==

=== Notwendige Einstellungen ===

Bedienung nur nach Einweisung (Wir geben Workshops!)

Wir empfehlen VisiCut und Inkscape, für Windows, Mac, und Linux. Anleitung: https://wiki.fablab-nuernberg.de/w/Nova_35#VisiCut

(Die vom Hersteller mitgelieferte Software für diesen Laser ist RDWORKS (nur Windows).
Dazu haben wir eine auch eine [https://raw.githubusercontent.com/jnweiger/ruida-laser/master/doc/laser-nova35-rdworks.md laser-nova35/HOWTO.txt] Checkliste.)

* Schneidfläche: 900 x 600 mm
* Laser-Leistung: ca 80 Watt

Material in die Mitte legen, grob nach Wellengitter ausrichten. Die Links-Hinten-Anschlagleisten die es beim Zing gab, gibt es hier nicht.
Es gibt links oben eine Ablage für Magnete und Eisengewichte, um Material unten zu halten.


Einschalten
-----------

* Display bleibt dunkel, bis Reset gedrückt wird. (Geht nur bei geschlossener Klappe)

Startpunkt Einstellung
----------------------

* Mit Cursor-Tasten hinfahren
* Startposition Taste (um die aktuelle Position als Startpunkt zu speichern)
** Achtung: Fährt manchmal sehr schnell. Die blaue Düse ist nur [ 20mm ] über dem Material. Sicher stellen, dass das nirgends kollidiert!

Focus Einstellung
-----------------

* Deckel auf. Warnleuchte beginnt zu blitzen, Reset leuchtet rot.
* Taste Z/U -> [z move] -> erst Cursor-Taste-rechts drücken. (= nach unten)
* Fokusmessung
** Weisses Plastikteil an roter Schnur
** 20mm Abstand zwischen Düsenspitze und Materialoberkante.
* ESC
* Deckel zu, Reset drücken. Warnleuchte wird wieder grün.

Laser Vorbereitung
------------------
* Datei übertragen (Netzwerk, USB-Kabel oder Stick)
* Taste [Startposition] (falls nicht vorher schon eingestellt)
* Taste [Box]
** Der rote Laserpunkt zeigt, ob alles draufpasst.
* Abluft
** Abluftschlauch am rechten Filterkasten anstecken.
** Abluftwarnschild in den Zing legen.
** Hauptschalter (rot) einschalten
** Kippschalter Aus/Auto/An auf Auto stellen
** Kippschalter Zing/Nova auf Nova stellen.

Lasern
------

* "Start/Pause" Taste drücken.
* Laser beginnt. (Prüfen, ob die Lüftung läuft)
* Uhr läuft inten links im Display mit.
* Nach dem Lasern ca. 30 sec warten, bis sich der Rauch verzogen hat.


==== Schneiden: CUT - ("Rote Linie") ====

Acryl Frequenz 1000 gibt bessere Schnitte als andere Frequenzen. Vielleicht hat die Frequenz aber auch gar keine Wirkung....

Die beiden Thunderlaser Nova35 in Nürnberg und Veitsbronn haben unterschiedliche Röhren. Die Werte hier sollten für beide funktionieren. In Veitsbronn kann man evtl ein wenig schneller fahren.

Die Geschwindigkeitsangaben (Speed [%]) gelten ab VisiCut 1.9. Im alten VisiCut 1.8 muss die Geschwindigkeit um 10 höher angegeben werden.

{| class="wikitable"
|-
! Material !! min power !! power !! speed !! frequency !! Bemerkung
|-
! !! [%] !! [%] !! [1/10 mm/s] !! [Hz] !! 
|-
| Acryl 2mm || 45 || 70 || 4 || 500 || jw 20211204 fln
|-
| Acryl 3mm || 55 || 70 || 2.5 || 500 || 
|-
| Acryl 4mm || 60 || 70 || 1.5 || 500 || 
|-
| Acryl 5mm || 65 || 70 || 1.0 || 500 || jw 2024-02-04
|-
| Acryl 6mm || 70 || 70 || 0.8 || 500 || jw 2022-02-14
|-
| Acryl 10mm || 70 || 70 || 0.7 || 500 || zweimal fahren mit langer Abkühlpause! jw 20211011 fln
|-
| Acryl 10mm || 70 || 70 || 0.5 || 500 || auf einmal durch! jw 20220824 fln
|-
|-
| Graupappe 0.25mm || 25 || 70 || 30 || 500 || ?
|-
| Graupappe 0.5mm || 28 || 70 || 20 || 500 || 
|-
| Graupappe 1.5mm || 35 || 70 || 10 || 500 || 
|-
| Graupappe 2.5mm || 50 || 70 || 6 || 500 || jw 20190722 falafue, 70 zu schnell.
|-
|-
| Kiefernbrettchen 5mm || 55 || 70 || 4 || 500 || ?
|-
| Kiefernbrettchen 8mm || 70 || 70 || 1 || 500 || ?
|-
|-
| Kraftplex 0.8mm || 27 || 70 || 14 || 500 || jw 20180901 falafue, 170 ist zu schnell
|-
| Kraftplex 1.0mm || 22 || 70 || 10 || 500 || jw fablab
|-
| Kraftplex 1.5mm || 20 || 70 || 5 || 500 || jw 20191101 fln
|-
| Kraftplex 3.0mm || 50 || 70 || 2.7 || 500 || jw 20180901 falafue
|-
|-
| Sperrholz Birke 3mm || 40 || 70 || 2 || 500 || war speed=30, jw 20231210 (stark schwankende Holzqualität zur Zeit)
|-
| Sperrholz Birke 4mm || 50 || 70 || 1.5 || 500 || war speed=20, jw 20221206
|-
| Sperrholz Birke 5mm || 60 || 70 || 1 || 500 || war speed=15, jw 20221206
|-
| Sperrholz Birke 6,5mm || 60 || 70 || 0.8 || 500 || 
|-
| Sperrholz Birke 8mm || 60 || 70 || 0.6 || 500 || jw 20201001 nbg
|-
|-
| Sperrholz Buche 1.5mm || 50 || 70 || 3 || 500 || jw 20190624 falafue Wasserfest verleimt?
|-
| Sperrholz Buche 4mm || 60 || 70 || 0.7 || 500 || jw 20220216 fln
|-
| Sperrholz Buche 6mm || 70 || 80 || 0.4 || 500 || unbedingt Abstandshölzer zwischen Werkstück und Gitter legen. Die Reflexionen brennen sich sonst ein.
|-
|-
| Sperrholz Kiefer 4mm || 60 || 80 || 1.2 || 500 || jw 20210429 nbg
|-
|-
| Sperrholz Linde 3mm || 40 || 70 || 4 || 500 || jw 20250416 nbg
|-
| Sperrholz Linde 4mm || 50 || 70 || 3 || 500 || 
|-
| Sperrholz Linde 5mm || 60 || 70 || 2 || 500 || 
|-
| Sperrholz Linde 6,5mm || 60 || 70 || 1.6 || 500 || 
|-
| Sperrholz Linde 8mm || 60 || 70 || 1.2 || 500 || 
|-
|-
| Sperrholz Pappel 2mm || 40 || 70 || 6 || 500 || 
|-
| Sperrholz Pappel 3mm || 40 || 70 || 5 || 500 || 
|-
| Sperrholz Pappel 4mm || 40 || 70 || 3.5 || 500 || jw 20190322 (speed=45 falafue)
|-
| Sperrholz Pappel 5mm || 50 || 70 || 2.5 || 500 || jw 20211105 fln
|-
| Sperrholz "Hornbach Pappel" 6mm || 60 || 70 || 1.2 || 500 || jw 20231009, 5-lagig, wasserfest, Seile
|-
| Sperrholz Pappel 6mm || 60 || 70 || 1.8 || 500 || jw 20211015 fln
|-
| Sperrholz Pappel 8mm || 60 || 70 || 1.3 || 500 || jw 20190815 falafue
|-
| Sperrholz Pappel 10mm || 60 || 70 || 1 || 500 || 
|-
| Sperrholz Gabun 2.5mm || 30 || 70 || 6 || 500 || jw 20230114
|-
|-
| Finnpappe 1mm || 26 || 65 || 6 || 500 || jw+vb 20260208
|-
| Finnpappe 2mm || 50 || 70 || 6 || 500 || 
|-
| Finnpappe 3mm || 50 || 70 || 8 || 500 || 
|-
|-
| Holzkarton 500g/m² 1mm || 20 || 40 || 7 || 500 || jst 20210312 fln
|-
| Kromapappe 2mm || 20 || 40 || 7 || 500 || 
|-
|-
| MDF Ikea 1.5mm || 30 || 70 || 8 || 500 || jw 20190513 falafue Verstopft die Lüftung in Nürnberg
|-
| MDF 3mm || 50 || 70 || 2.2 || 500 || jw 20180505: Verstopft die Lüftung in Nürnberg
|-
|-
| POM Delrin 6.0mm || 50 || 70 || 0.8 || 500 || jw 20181001 falafue, verklebt immernoch
|-
| POM Delrin 4.0mm || 50 || 70 || 1.2 || 500 || jw 20181001 falafue
|-
|-
| PU Weichschaum 10mm || 50 || 70 || 10 || 500 || 
|-
| Depron Schaum 3mm || 11 || 20 || 20 || 500 || jw 20220519
|-
| Depron Schaum 6mm || 15 || 45 || 20 || 500 || jw 20220519
|-
| Airplak Kartonschaum 3mm || 20 || 70 || 15 || 500 || jw 20191216 falafue
|-
|-
| Schichtstoff (HPL) 0.8mm || 50 || 70 || 5 || 500 || jw 20181008 falafue, stinkt metallisch, Vorsicht: giftige Dämpfe!
|-
| PET Folie 0.5mm || 28 || 70 || 15 || 500 || jw 2020-04-28, fln
|-
| Baumwollstoff 0.5mm || 28 || 70 || 20 || 500 || jw+vb 2020-08-07, fln, Stoff wurde zuvor gefaltet und gepresst
|-
| Papier 0.1 mm || 10 || 40 || 25 || 1500 || 
|}
Falls diese Einstellungen nicht ganz durch schneiden: '''Bitte Linse reinigen!'''

==== Markieren: MARK - ("Grüne Linie") ====
{| class="wikitable"
|-
! Material !! min power !! power !! speed !! frequency !! Bemerkung
|-
! !! [%] !! [%] !! [1/10 mm/s] !! [Hz] !! 
|-
|-
| Acryl || 9 ||20 || 20 || 500 || jw 2023-12-17
|-
| Birke || 7 || 10 || 10 || 500 || jw 2021-08-01: feinstmögliche Markierlinie
|-
| Birke || 9 || 35 || 20 || 500 || jw 20180824: max 30 war zu wenig, min 9 ist sehr viel
|-
| Buche || 8 || 25 || 100 || 500 || jw 20190624: Beschriftung recht blass
|-
| Gabun || 10 || 20 || 20 || 500 || jw 20230114 sehr dunkel und tief
|-
| Linde || 9 || 35 || 40 || 500 || jw 20250416 nbg
|-
| Graupappe || 9 || 35 || 25 || 500 || jw+dagmar 20240316
|-
| Kiefernbrettchen || 9 || 20 || 25 || 500 || ?
|-
| Smarties || 20 || 25 || 100 || 500 || jw 20190405 (Zuckerglasur, ohne Schokalade zu treffen)
|-
| Kraftplex || 9 || 25 || 20 || 500 || jw 20191101 fln, 8 zündet sauber in Nürnberg
|-
| Airplak Kartonschaum || 9 || 15 || 25 || 500 || jw 20191216 falafue (schneidet den obere Karton)
|-
|}

==== Gravieren: ENGRAVE - ("Schwarze Fläche") ====
{| class="wikitable"
|-
! Material !! min power !! power !! Speed !! frequency !! Bemerkung
|-
! !! [%] !! [%] !! [1/10 mm/s] !! [Hz] !! 
|-
|-
| Acryl || 10 || 50 || 90 || 500 || 20240211 vb
|-
| Apfel || 10 || 10 || 90 || 500 || jw 20220530: 0.2mm tief (200dpi, 500dpi scheint egal)
|-
| Birke || 10 || 25 || 30 || 500 || 
|-
| Birke || 10 || 70 || 90 || 500 || Tief. Im Sperrholz bis zur ersten Kleberschicht.
|-
| Gabun || 10 || 12 || 80 || 500 || Floyd-Steinberg Korrektur -100 .. -140
|-
| HPL || 10 || 35 || 20 || 500 || High Pressure Laminate, Vorsicht: giftige Dämpfe
|-
| Flusskiesel || 60 || 70 || 5 || 500 || 20230721 vb auf ausreichende Liniendicke achten
|-
| Linde || 10 || 70 || 60 || 500 || 20260208 jw, ca. 1 mm tief (Speed 30 für 2mm)
|-
| Papier || 10 || 10 || 100 || 1500 || 
|-
| Büttenpapier 300g || 10 || 60 || 80 || 500 || 20260208 jw für Martin "Arches", eng-fs-200
|-
| Papier 250g || 20 || 50 || 80 || 500 || 20260208 jw für Martin "LineArt 250", eng-fs-200
|-
| Weinglas || 10 || 20 || 90 || 500 || 20250427 vb mit Rotationsachse
|-
| Pulverbeschichtung || 45 || 50 || 100 || 500 || 20251120 vb mit Rotationsachse
|}

=== Action ===

== Rotationsachse ==

Für den Nova gibt es im FabLab eine Rotationsachse, mit der Zylinder graviert werden können. Die Rotationsachse ersetzt die Y-Achse.

Durch den aktuell notwendigen Skalierungsfaktor stimmt die Oberflächengeschwindigkeit auf der Rotationsachse nicht. Daher werden Linien in Y-Richtung mit etwas anderer Leistung pro Strecke gelasert als in X-Richtung. Beim Gravieren spielt das aber keine Rolle und muss nur bei Cut und Mark beachtet werden.

=== Vorbereitung ===
# Laser normal einschalten
# Die Y-Achse ungefähr in die Mitte bewegen
# Laserbett ausreichend tief fahren(!)
# Rotationsachse mit dem Anschluss nach Vorne in der Laser stellen, anschließen und Schalter neben dem Anschluss betätigen
# Mit geschlossenem Deckel auf dem Bedienfeld "Reset" drücken und warten bis sich beide Achsen nicht mehr bewegen.

=== VisiCut ===
Objekte müssen in der Y-Achse skaliert (verzogen) werden, damit die Maße auf dem Zylinder passen. Aktuell gibt es dafür noch keine VisiCut Funktionalität.

# Objekte importieren
# Objekte 90° gegen den Uhrzeigersinn drehen, so dass Objekt-Oben in VisiCut nach Links zeigt
# Objekte über das "Position"-Tab auf der rechten Seite skalieren:
#* "proportional" darf nicht ausgewählt sein
#* "height" mit 1,2688 multiplizieren

=== Abschluss ===
Rotationsachse entfernen und Schalter wieder auf "0" stellen(!!).

== Nachbereitung ==

Nach dem Lasern ca. 30 Sekunden warten, bis sich der Rauch verzogen hat.

=== Maschine abschalten ===

=== Aufräumen ===


[[Kategorie:Geräte]]
[[Kategorie:Lasercutter]]
