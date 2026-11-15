// StackChan (kit oficial M5Stack, CoreS3) para el Panel Elite
// CMDR ORTEM ED DER y Claude
// Recibe los avisos del panel v1.1.2+ por UDP 5007 (12 AJUSTES > ROBOT). No necesita EMITIR.
// v1.1.8: caras para BODEGA LLENA, PASAJEROS, CONSTRUCCION TERMINADA, NO VENDER y avisos de RUTA.
// v1.1.10: susto con la PARADA DE EMERGENCIA; con la bodega llena enseña cajas apiladas (las manda el panel).
// v1.1.9: compañero de viaje: copiloto en ruta, mapas, ventas, misiones, descanso, resumen, ascensos,
//         sistemas CDSN, se duerme en el menu, tocar la cabeza repite el ultimo aviso y letra mas pequeña.
static const char* ROBOT_VER = "v1.1.10";   // (SC_VERSION choca con la libreria smartconfig del ESP32)
#include <M5StackChan.h>
#include <Avatar.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ---------- CONFIGURA ----------
const char* WIFI_SSID = "TU_WIFI";
const char* WIFI_PASS = "TU_CLAVE";
const int UDP_PORT = 5007;
// Cabeza: decimas de grado. X -1280..1280 (izq/dcha), Y 0..900 (0 = abajo, 900 = arriba)
const int CX = 0, CY = 300;          // postura de reposo (ajusta CY si mira muy bajo/alto)
const int Y_MIN = 180, Y_MAX = 850;  // abajo no de 18 grados: si no, la cabeza golpea los pies
const uint8_t BRILLO = 120;          // brillo maximo de los LED (0-255)
const unsigned long TIEMPO_X = 3;   // v1.1.9: cuanto se quedan los textos (x1 = como antes, x3 = el triple)
// --------------------------------

using namespace m5avatar;
Avatar avatar;

WiFiUDP udp;
IPAddress panelIP;
bool panelVivo = false;
bool saludado = false;          // saluda solo la primera vez que encuentra el panel
unsigned long tToque = 0;
unsigned long finFoto = 0;                 // mientras se ve una foto, la cara espera
bool peligro = false; String motivo;       // escudos caidos o casco < 70 %
bool recarga = false; String recTxt;       // recogiendo combustible
bool aPie = false; String clima;           // a pie; clima "frio" / "calor" / ""
String mapa;                               // v1.1.9: mapa abierto en el juego: "gal" / "sis" / ""
String cop;                                // v1.1.9: copiloto en ruta (saltos, combustible, siguiente estrella)
bool dormido = false;                      // v1.1.9: juego en el menu o cerrado
unsigned long finAtq = 0; int avAtq = 0;   // v1.1.9: cuenta atras del atraque (millis en que acaba)
bool noche = false; uint8_t brillo = BRILLO; // v1.1.9: modo noche (menos luz y menos volumen)
uint8_t brilloPantalla = 128;
// v1.1.9: preguntas por voz (tocar la pantalla). Graba aqui, el panel lo entiende y contesta.
const int OIR_SEG = 4, OIR_RATE = 16000;
int16_t* oirBuf = nullptr;                 // 4 s de audio (128 KB en la PSRAM)
uint8_t* vozBuf = nullptr; int vozLen = 0; // la voz de la respuesta
unsigned long tFotoFuera = 0;
String ultTxt; unsigned long tUlt = 0;     // v1.1.9: ultimo aviso (tocar la cabeza lo repite)
String pendEv, pendKind, pendTit, pendDat; bool pend = false;
unsigned long tHola = 0, finHabla = 0, finTexto = 0, tIdle = 0;
String texto;

// ---------- tipos (aqui arriba para que el Arduino IDE los vea antes que las funciones) ----------
struct Paso { int x, y, vel, ms; };
enum Luz { L_REPOSO, L_ALARMA, L_SALTO, L_BIEN, L_TRISTE, L_APAGADO, L_RECARGA };

// ---------- cabeza: secuencias de pasos ----------
Paso cola[8]; int nPasos = 0, iPaso = 0; unsigned long tPaso = 0;

void secuencia(std::initializer_list<Paso> p) {
  nPasos = 0;
  for (auto& s : p) if (nPasos < 8) cola[nPasos++] = s;
  iPaso = 0; tPaso = 0;
}

void mover(const char* m) {
  if (!strcmp(m, "asentir"))      secuencia({{CX,CY+250,700,220},{CX,Y_MIN,700,220},{CX,CY+250,700,220},{CX,CY,500,300}});
  else if (!strcmp(m, "negar"))   secuencia({{CX-300,CY,500,350},{CX+300,CY,500,450},{CX-300,CY,500,450},{CX,CY,400,400}});
  else if (!strcmp(m, "mirar"))   { int x = random(-450, 450); secuencia({{x,CY+(int)random(0,250),350,900},{CX,CY,300,800}}); }
  else if (!strcmp(m, "temblar")) secuencia({{CX-120,CY,1000,90},{CX+120,CY,1000,90},{CX-120,CY,1000,90},{CX+120,CY,1000,90},{CX,CY,800,150}});
  else if (!strcmp(m, "aviso"))   secuencia({{CX-60,CY,600,150},{CX+60,CY,600,200},{CX,CY,500,200}});
  else if (!strcmp(m, "alzar"))   secuencia({{CX,CY+450,500,600},{CX,CY,300,600}});
  else if (!strcmp(m, "dormir"))  secuencia({{CX,Y_MIN,150,1500}});
}

void motorCabeza(unsigned long t) {
  if (iPaso >= nPasos || t < tPaso) return;
  Paso& p = cola[iPaso++];
  M5StackChan.Motion.move(p.x, constrain(p.y, Y_MIN, Y_MAX), p.vel);
  tPaso = t + p.ms;
}

// ---------- LED RGB (0-5 izquierda, 6-11 derecha) ----------
Luz luz = L_APAGADO; unsigned long tLuz = 0, finLuz = 0;

void ponLuz(Luz l, unsigned long dur) { luz = l; tLuz = millis(); finLuz = dur ? tLuz + dur : 0; }

void pintaLuz(unsigned long t) {
  static unsigned long tRef = 0;
  if (t - tRef < 30) return;
  tRef = t;
  if (finLuz && t > finLuz) { luz = peligro ? L_ALARMA : recarga ? L_RECARGA : panelVivo ? L_REPOSO : L_APAGADO; finLuz = 0; }
  float e = (t - tLuz) / 1000.0f;
  for (int i = 0; i < 12; i++) {
    uint8_t r = 0, g = 0, b = 0;
    switch (luz) {
      case L_REPOSO: {            // naranja Elite respirando suave
        float k = 0.10f + 0.08f * sinf(e * 1.5f);
        r = brillo * k; g = brillo * k * 0.35f; break; }
      case L_ALARMA: {            // rojo parpadeando, alterna lados
        bool on = ((int)(e * 6) + (i < 6 ? 0 : 1)) % 2;
        r = on ? brillo : 0; break; }
      case L_SALTO: {             // azul que recorre la tira
        int pos = (int)(e * 14) % 6;
        int j = i < 6 ? i : 11 - i;
        float k = j == pos ? 1.0f : (abs(j - pos) == 1 ? 0.3f : 0.05f);
        r = brillo * k * 0.2f; g = brillo * k * 0.5f; b = brillo * k; break; }
      case L_BIEN: {              // verde que se apaga poco a poco
        float k = max(0.1f, 1.0f - e / 4.0f);
        g = brillo * k; b = brillo * k * 0.2f; break; }
      case L_RECARGA: {           // amarillo que se llena desde abajo
        int nivel = (int)(e * 4) % 7;
        int j = i < 6 ? i : 11 - i;
        float k = j < nivel ? 1.0f : 0.1f;
        r = brillo * k; g = brillo * k * 0.75f; break; }
      case L_TRISTE: {            // violeta tenue
        float k = 0.25f + 0.15f * sinf(e * 2.0f);
        r = brillo * k * 0.5f; b = brillo * k; break; }
      default: break;
    }
    M5StackChan.setRgbColor(i, r, g, b);
  }
  M5StackChan.refreshRgb();
}

// ---------- textos ----------
String sinTildes(String s) {
  const char* de[] = {"Á","É","Í","Ó","Ú","Ü","Ñ","á","é","í","ó","ú","ü","ñ","·","»","«"};
  const char* a[]  = {"A","E","I","O","U","U","N","a","e","i","o","u","u","n","-",">","<"};
  for (int i = 0; i < 17; i++) s.replace(de[i], a[i]);
  return s;
}

bool tiene(const String& t, std::initializer_list<const char*> pals) {
  for (auto p : pals) if (t.indexOf(p) >= 0) return true;
  return false;
}

// v1.1.9c: el bocadillo es de UNA linea: el texto va seguido y, si no cabe, se desplaza (marquesina)
const int VENTANA = 24;                    // letras que caben en el bocadillo
String linea, ventana; int scrollPos = 0; unsigned long tScroll = 0;

String unaLinea(const String& s) { String r = s; r.replace("\n", " - "); r.trim(); return r; }

void ponTexto(const String& s) {
  String l = unaLinea(s);
  texto = l;
  if (l == linea) return;
  linea = l; scrollPos = 0; tScroll = millis() + 1500;          // pausa al principio para leerlo
  ventana = (int)l.length() > VENTANA ? l.substring(0, VENTANA) : l;
  avatar.setSpeechText(ventana.c_str());
}

void scrollTexto(unsigned long t) {
  if ((int)linea.length() <= VENTANA || t < tScroll) return;
  tScroll = t + 260;
  String vuelta = linea + "   ***   " + linea;
  scrollPos = (scrollPos + 1) % (linea.length() + 9);
  if (scrollPos == 0) tScroll = t + 1500;                        // al volver al principio, otra pausa
  ventana = vuelta.substring(scrollPos, scrollPos + VENTANA);
  avatar.setSpeechText(ventana.c_str());
}

void pon() { ponTexto(texto); }

void decir(Expression cara, const String& txt, const char* mov, unsigned long ms) {
  avatar.setExpression(cara);
  texto = txt; pon();
  mover(mov);
  unsigned long t = millis();
  finHabla = t + 1500; finTexto = t + ms * TIEMPO_X; tIdle = t;
}

// ---------- reaccion a un aviso del panel ----------
// tipos de aviso del panel (EV_LIST): la cara se elige por el tipo; si no se conoce, por el texto
bool es(const String& ev, std::initializer_list<const char*> l) {
  for (auto p : l) if (ev == p) return true;
  return false;
}

void reaccionar(const String& ev, const String& kind, String titulo, String dato) {
  titulo = sinTildes(titulo); dato = sinTildes(dato);
  String T = titulo; T.toUpperCase();
  String txt = dato.length() ? titulo + "\n" + dato : titulo;
  bool cdsn = tiene(T, {"CDSN", "CABALLEROS", "TOMAIS", "CONSEGUIDA", "EXPANSION"}) || tiene(dato, {"CDSN", "Caballeros"});

  ultTxt = txt; tUlt = millis();                                   // v1.1.9: para repetirlo tocando la cabeza

  // v1.1.10: parada de emergencia (te has acercado demasiado rapido a una estrella o un planeta): susto
  if (es(ev, {"emergstop"})) {
    decir(Expression::Doubt, txt, "temblar", 8000); ponLuz(L_ALARMA, 6000);
    M5.Speaker.tone(1500, 150); delay(160); M5.Speaker.tone(1000, 150); delay(160); M5.Speaker.tone(600, 300);
    return;
  }

  // v1.1.9: compañero de viaje
  if (es(ev, {"robhito"})) {                                       // ascenso o primer descubrimiento: fanfarria
    decir(Expression::Happy, txt, "alzar", 8000);   ponLuz(L_BIEN, 8000);
    M5.Speaker.tone(1600, 100); delay(110); M5.Speaker.tone(2000, 100); delay(110); M5.Speaker.tone(2400, 300);
    return;
  }
  if (es(ev, {"robllegada"})) {                                   // final de la ruta
    decir(Expression::Happy, txt, "alzar", 7000);   ponLuz(L_BIEN, 6000);
    M5.Speaker.tone(2000, 90); delay(100); M5.Speaker.tone(2600, 90); delay(100); M5.Speaker.tone(3200, 200);
    return;
  }
  if (es(ev, {"robresumen"})) {                                    // resumen de la partida al atracar
    decir(Expression::Happy, txt, "asentir", 8000); ponLuz(L_BIEN, 4000);   M5.Speaker.tone(2200, 80);
    return;
  }
  if (es(ev, {"robdescanso"})) {                                   // 2 h jugando: bostezo
    decir(Expression::Sleepy, txt, "asentir", 9000); ponLuz(L_RECARGA, 5000); M5.Speaker.tone(700, 250);
    return;
  }
  if (es(ev, {"robmision", "robexplo", "fuelroute"})) {            // misiones, datos sin vender, combustible justo
    decir(Expression::Doubt, txt, "aviso", 8000);   ponLuz(L_RECARGA, 5000); M5.Speaker.tone(900, 150);
    return;
  }
  if (es(ev, {"robcdsn"})) {                                       // llegada a un sistema de CDSN
    if (kind == "alarm") { decir(Expression::Doubt, txt, "aviso", 7000); ponLuz(L_RECARGA, 4000); M5.Speaker.tone(900, 150); }
    else                 { decir(Expression::Happy, txt, "alzar", 7000); ponLuz(L_BIEN, 4000);   M5.Speaker.tone(2600, 120); }
    return;
  }

  // avisos nuevos del panel v1.1.1 - v1.1.8
  if (es(ev, {"colfin"})) {                                        // construccion terminada: gran celebracion
    decir(Expression::Happy, txt, "alzar", 9000);   ponLuz(L_BIEN, 9000);
    M5.Speaker.tone(1800, 120); delay(130); M5.Speaker.tone(2400, 120); delay(130); M5.Speaker.tone(3000, 250);
    return;
  }
  if (es(ev, {"paxentrega", "paxin"})) {                           // pasajeros a bordo / entregados
    decir(Expression::Happy, txt, "asentir", 6000); ponLuz(L_BIEN, 4000);   M5.Speaker.tone(2400, 100);
    return;
  }
  if (es(ev, {"bodegallena"})) {                                   // bodega llena: aviso amarillo
    decir(Expression::Doubt, txt, "aviso", 5000);   ponLuz(L_RECARGA, 3000); M5.Speaker.tone(900, 150);
    return;
  }
  if (es(ev, {"colventa", "rutapeligro", "rutacdsn", "paxbuscado", "paxtiempo"})) {   // no vender, estrella peligrosa, guerra, pasajeros
    decir(Expression::Angry, txt, ev == "colventa" ? "negar" : "temblar", 6000); ponLuz(L_ALARMA, 4000); M5.Speaker.tone(1200, 120);
    return;
  }
  if (es(ev, {"rutafin"})) {                                       // quedan 2 saltos
    decir(Expression::Doubt, txt, "mirar", 5000);   ponLuz(L_SALTO, 4000);  M5.Speaker.tone(1600, 80);
    return;
  }
  if (es(ev, {"venta"})) {                                         // v1.1.9: venta en el mercado, caja registradora
    decir(Expression::Happy, txt, "alzar", 6000);   ponLuz(L_BIEN, 4000);
    M5.Speaker.tone(2600, 70); delay(80); M5.Speaker.tone(3400, 140);
    return;
  }

  if (es(ev, {"died", "rebuy", "missionexp"}) || tiene(T, {"DESTRUID", "HAS CAIDO", "CAJA NEGRA", "PERDEIS", "SIN EXITO"})) {
    decir(Expression::Sad, txt, "negar", 7000);    ponLuz(L_TRISTE, 7000); M5.Speaker.tone(400, 300);
  } else if (es(ev, {"sessend"})) {
    decir(Expression::Sleepy, txt, "dormir", 6000); ponLuz(L_TRISTE, 3000);
  } else if (es(ev, {"interdicted", "underattack", "shields_down", "hull", "heat", "hplow", "oxy", "temp", "jetdmg",
                     "scanned", "wanted", "cmdrtarget", "crime", "shutdown", "tgwar", "thargmusic", "moddmg",
                     "power", "gravity", "srvfuel", "risk", "lowcons", "facwar"})
             || (ev == "" && (kind == "red" || kind == "alarm") && !cdsn)) {
    decir(Expression::Angry, txt, "temblar", 6000); ponLuz(L_ALARMA, 4000); M5.Speaker.tone(1200, 120);
  } else if (es(ev, {"jump", "arrive", "fuelroute", "jetcone", "taxi", "dropship"}) || kind == "jump") {
    decir(Expression::Doubt, txt, "mirar", 6000);   ponLuz(L_SALTO, 6000);  M5.Speaker.tone(1600, 80);
  } else if (cdsn || es(ev, {"find", "codex", "cg", "opend", "shiparrived"})) {
    decir(Expression::Happy, txt, "alzar", 7000);   ponLuz(L_BIEN, 5000);   M5.Speaker.tone(2600, 120);
  } else {
    decir(Expression::Happy, txt, "asentir", 6000); ponLuz(L_BIEN, 4000);   M5.Speaker.tone(2200, 80);
  }
}

// ---------- fotos del panel (estacion, nave, logo de la faccion) ----------
bool bajarFoto(const String& f, int port, uint8_t*& buf, int& len) {
  HTTPClient http;
  http.setTimeout(3000);
  String url = "http://" + panelIP.toString() + ":" + String(port) + "/foto?f=" + f;
  if (!http.begin(url) || http.GET() != 200) { http.end(); return false; }
  len = http.getSize();
  if (len <= 0 || len > 200000) { http.end(); return false; }
  buf = (uint8_t*)ps_malloc(len);
  if (!buf) { http.end(); return false; }
  WiFiClient* st = http.getStreamPtr();
  int got = 0; unsigned long t0 = millis();
  while (got < len && millis() - t0 < 4000) {
    int a = st->available();
    if (a > 0) got += st->readBytes(buf + got, min(a, len - got));
    else delay(2);
  }
  http.end();
  if (got < len) { free(buf); buf = nullptr; return false; }
  return true;
}

void ensenarFoto(const String& f, int port, String tit, String dat, int seg, bool rotulada) {
  uint8_t* buf = nullptr; int len = 0;
  if (!bajarFoto(f, port, buf, len)) return;
  avatar.suspend();
  delay(60);
  auto& d = M5.Display;
  d.drawJpg(buf, len, 0, 0, 320, 240);
  free(buf);
  tit = sinTildes(tit); dat = sinTildes(dat);
  if (!rotulada && (tit.length() || dat.length())) {  // rotulo abajo (v1.1.9c: ya lo trae la foto del panel)
    int h = dat.length() ? 44 : 26;
    d.fillRect(0, 240 - h, 320, h, TFT_BLACK);
    d.drawFastHLine(0, 240 - h, 320, 0xFC60);
    d.setTextSize(1); d.setFont(&fonts::DejaVu18);
    d.setTextColor(0xFC60, TFT_BLACK);               // naranja Elite
    d.setTextDatum(top_left);
    d.drawString(tit.substring(0, 34), 6, 240 - h + 4);
    if (dat.length()) { d.setTextColor(TFT_WHITE, TFT_BLACK); d.drawString(dat.substring(0, 34), 6, 240 - h + 24); }
  }
  finFoto = millis() + seg * 1000UL;
  ponLuz(f == "logo" ? L_ALARMA : L_BIEN, seg * 1000UL);
  M5.Speaker.tone(1800, 60);
}

void quitarFoto() {
  finFoto = 0; tFotoFuera = millis();
  avatar.resume();
  if (pend) { pend = false; reaccionar(pendEv, pendKind, pendTit, pendDat); }
}

// ---------- peligro continuo ----------
// color de la cara: 0 normal, 1 roja (peligro), 2 amarilla (recargando), 3 verde (a pie), 4 azul (frio), 5 naranja (calor)
int colorCara = 0;
void ponColorCara(int c) {
  if (c == colorCara) return;
  colorCara = c;
  ColorPalette cp;
  // 0 negro, 1 rojo peligro, 2 amarillo recarga, 3 verde a pie, 4 azul frio, 5 naranja calor, 6 azul oscuro mapa (v1.1.9)
  const uint16_t fondos[] = {TFT_BLACK, 0xC000, 0xFE00, 0x2D84, 0x3B3F, 0xFC00, 0x08CA};
  uint16_t fondo = fondos[constrain(c, 0, 6)];
  cp.set(COLOR_PRIMARY, (c == 0 || c == 6) ? TFT_WHITE : TFT_BLACK);   // ojos y boca: blancos en fondo oscuro
  cp.set(COLOR_BACKGROUND, fondo);
  cp.set(COLOR_BALLOON_FOREGROUND, TFT_BLACK);
  cp.set(COLOR_BALLOON_BACKGROUND, TFT_WHITE);
  avatar.setColorPalette(cp);
}


// color segun el estado (el peligro manda sobre todo)
int colorBase() {
  if (mapa.length()) return 6;                       // v1.1.9: mapa abierto
  if (recarga) return 2;
  if (aPie) return clima == "frio" ? 4 : clima == "calor" ? 5 : 3;
  return 0;
}

void ponPie(bool pie, const String& c) {
  if (pie == aPie && c == clima) return;
  aPie = pie; clima = c;
  if (!peligro) ponColorCara(colorBase());
}

void ponPeligro(bool on, const String& m) {
  if (on == peligro && m == motivo) return;
  bool empieza = on && !peligro;
  peligro = on;
  ponColorCara(on ? 1 : colorBase()); motivo = sinTildes(m);
  if (peligro) {
    avatar.setExpression(Expression::Angry);
    texto = motivo; pon();
    ponLuz(L_ALARMA, 0);
    if (empieza) { mover("aviso"); M5.Speaker.tone(1200, 150); }    // un solo gesto corto al empezar
    finTexto = 0;
  } else if (recarga) {
    avatar.setExpression(Expression::Happy);
    texto = recTxt; pon(); finTexto = 0;
    ponLuz(L_RECARGA, 0);
  } else if (mapa.length()) {
    avatar.setExpression(Expression::Doubt);
    texto = textoMapa(); pon(); finTexto = 0;
    ponLuz(L_SALTO, 0);
  } else {
    avatar.setExpression(Expression::Happy);
    texto = "Peligro superado"; pon();
    ponLuz(L_BIEN, 3000); mover("asentir");
    finTexto = millis() + 3000; tIdle = millis();
  }
}

void ponRecarga(bool on, const String& txt) {
  if (on == recarga && txt == recTxt) return;
  bool empieza = on && !recarga;
  recarga = on; recTxt = txt;
  if (peligro) return;                               // el peligro manda
  ponColorCara(colorBase());
  if (on) {
    avatar.setExpression(Expression::Happy);
    texto = recTxt; pon(); finTexto = 0;
    ponLuz(L_RECARGA, 0);
    if (empieza) M5.Speaker.tone(2000, 60);
  } else {
    avatar.setExpression(Expression::Neutral); ponTexto(""); finTexto = 0;
    ponLuz(L_BIEN, 2000);
  }
}

// v1.1.9: mapa galactico o del sistema abierto: cara de duda mirando a los lados
String textoMapa() { return mapa == "gal" ? "Mapa galactico" : "Mapa del sistema"; }

void ponMapa(const String& m) {
  if (m == mapa) return;
  mapa = m;
  if (peligro) return;                               // el peligro manda
  ponColorCara(colorBase());
  if (mapa.length()) {
    avatar.setExpression(Expression::Doubt);
    texto = textoMapa(); pon(); finTexto = 0;
    ponLuz(L_SALTO, 0); mover("mirar"); tIdle = millis();
  } else if (recarga) {
    avatar.setExpression(Expression::Happy);
    texto = recTxt; pon(); finTexto = 0;
    ponLuz(L_RECARGA, 0);
  } else {
    avatar.setExpression(Expression::Neutral); ponTexto(""); finTexto = 0;
    ponLuz(L_REPOSO, 0);
  }
}

// v1.1.9: juego en el menu o cerrado: se duerme; al volver, se despierta
void ponDormido(bool on) {
  if (on == dormido) return;
  dormido = on;
  if (on) {
    peligro = false; recarga = false; mapa = ""; ponColorCara(0);
    avatar.setExpression(Expression::Sleepy); texto = "Zzz..."; pon(); finTexto = 0;
    ponLuz(L_TRISTE, 0); mover("dormir");
  } else {
    decir(Expression::Happy, "o7 De vuelta, Comandante", "alzar", 3000);
    ponLuz(L_BIEN, 2000);
  }
}

// v1.1.9: cuenta atras del atraque (el panel manda los segundos; el robot cuenta solo)
void ponAtraque(int seg) {
  if (seg <= 0) {
    if (finAtq) { finAtq = 0; if (!finTexto && !peligro) { avatar.setExpression(Expression::Neutral); ponTexto(""); } }
    return;
  }
  unsigned long fin = millis() + seg * 1000UL;
  if (!finAtq) { avAtq = seg > 60 ? 0 : 1; M5.Speaker.tone(2000, 60); }
  finAtq = fin;
}

// v1.1.9: modo noche, de 23 a 8 h: luces, pantalla y pitidos mas suaves
void ponNoche(bool on) {
  if (on == noche) return;
  noche = on;
  brillo = on ? BRILLO / 4 : BRILLO;
  M5.Speaker.setVolume(on ? 30 : 90);
  M5.Display.setBrightness(on ? brilloPantalla / 3 : brilloPantalla);
}

// ---------- v1.1.9: preguntas por voz ----------
bool bajarVoz(const String& ruta) {
  HTTPClient http;
  http.setTimeout(5000);
  if (!http.begin("http://" + panelIP.toString() + ":8081" + ruta) || http.GET() != 200) { http.end(); return false; }
  int len = http.getSize();
  if (len <= 44 || len > 600000) { http.end(); return false; }
  uint8_t* b = (uint8_t*)ps_malloc(len);
  if (!b) { http.end(); return false; }
  WiFiClient* st = http.getStreamPtr();
  int got = 0; unsigned long t0 = millis();
  while (got < len && millis() - t0 < 8000) {
    int a = st->available();
    if (a > 0) got += st->readBytes(b + got, min(a, len - got));
    else delay(2);
  }
  http.end();
  if (got < len) { free(b); return false; }
  vozBuf = b; vozLen = len;
  return true;
}

void preguntar() {
  if (vozBuf && !M5.Speaker.isPlaying()) { free(vozBuf); vozBuf = nullptr; }
  if (vozBuf) return;                                    // todavia esta hablando
  const size_t n = (size_t)OIR_SEG * OIR_RATE;
  if (!oirBuf) oirBuf = (int16_t*)ps_malloc(n * 2);
  if (!oirBuf) { decir(Expression::Sad, "Sin memoria para oir", "negar", 3000); return; }

  avatar.setExpression(Expression::Doubt); texto = "Te escucho..."; pon(); finTexto = 0;
  ponLuz(L_SALTO, 0); M5StackChan.Motion.move(CX, CY + 150, 400);
  M5.Speaker.tone(2400, 80); delay(150);
  while (M5.Speaker.isPlaying()) delay(5);
  M5.Speaker.end();                                      // altavoz y microfono no pueden ir a la vez
  M5.Mic.begin();
  const size_t TROZO = 1600;                             // 0,1 s
  for (size_t i = 0; i < n; i += TROZO) M5.Mic.record(oirBuf + i, min(TROZO, n - i), OIR_RATE);
  while (M5.Mic.isRecording()) delay(5);
  M5.Mic.end();
  M5.Speaker.begin(); M5.Speaker.setVolume(noche ? 30 : 90);
  M5.Speaker.tone(1800, 60);

  texto = "Pensando..."; pon(); ponLuz(L_RECARGA, 0);
  HTTPClient http;
  http.setTimeout(25000);                                // en la Pi 3 tarda mas
  String body;
  if (http.begin("http://" + panelIP.toString() + ":8081/oir?r=" + String(OIR_RATE))) {
    http.addHeader("Content-Type", "application/octet-stream");
    if (http.POST((uint8_t*)oirBuf, n * 2) == 200) body = http.getString();
  }
  http.end();
  M5StackChan.Motion.move(CX, CY, 300);
  JsonDocument doc;
  if (!body.length() || deserializeJson(doc, body)) {
    decir(Expression::Sad, "No llego al panel", "negar", 4000); ponLuz(L_TRISTE, 3000); return;
  }
  String txt = sinTildes(String((const char*)(doc["txt"] | "")));
  bool ok = String((const char*)(doc["cara"] | "")) == "ok";
  String wav = (const char*)(doc["wav"] | "");
  if (wav.length()) bajarVoz(wav);
  decir(ok ? Expression::Happy : Expression::Doubt, txt, ok ? "asentir" : "negar", 8000);
  ponLuz(ok ? L_BIEN : L_REPOSO, 3000);
  ultTxt = txt; tUlt = millis();
  if (vozBuf) {
    uint32_t rate = vozBuf[24] | (vozBuf[25] << 8) | (vozBuf[26] << 16) | (vozBuf[27] << 24);
    if (!rate) rate = 22050;
    M5.Speaker.playWav(vozBuf, vozLen);
    finHabla = millis() + (unsigned long)((vozLen - 44) * 1000ULL / (rate * 2));   // la boca se mueve mientras habla
  }
}

// ---------- escuchar al panel ----------
void escuchar(unsigned long t) {
  int len;
  while ((len = udp.parsePacket()) > 0) {
    static char buf[1024];
    int n = udp.read(buf, sizeof(buf) - 1);
    if (n <= 0) continue;
    buf[n] = 0;
    IPAddress ip = udp.remoteIP();
    panelIP = ip;
    udp.beginPacket(ip, UDP_PORT); udp.print("STACKCHAN-OK"); udp.endPacket();   // "aqui estoy"

    JsonDocument doc;
    if (deserializeJson(doc, buf)) continue;
    tHola = t;
    if (!panelVivo) {
      panelVivo = true;
      if (!saludado) {
        saludado = true;
        decir(Expression::Happy, "o7 Comandante\nPanel " + String((const char*)(doc["ver"] | "")), "asentir", 4000);
        ponLuz(L_BIEN, 3000);
      } else {                                  // vuelve tras un corte: sin saludo
        avatar.setExpression(Expression::Neutral); ponTexto(""); finTexto = 0;
        ponLuz(L_REPOSO, 0); M5StackChan.Motion.move(CX, CY, 300);
      }
    }
    String tipo = doc["t"] | "";
    if (tipo == "peligro" || tipo == "hola") {
      if (tipo == "peligro" || doc["peligro"].is<bool>()) ponPeligro(doc[tipo == "peligro" ? "on" : "peligro"] | false, doc["motivo"] | "");
      if (doc["recarga"].is<bool>()) ponRecarga(doc["recarga"] | false, doc["rectxt"] | "");
      if (doc["pie"].is<bool>()) ponPie(doc["pie"] | false, doc["clima"] | "");
    }
    if ((tipo == "mapa" || tipo == "hola") && doc["mapa"].is<const char*>()) ponMapa(doc["mapa"] | "");
    if (tipo == "hola" && doc["cop"].is<const char*>()) cop = sinTildes(doc["cop"] | "");
    if (tipo == "hola" && doc["zzz"].is<bool>()) ponDormido(doc["zzz"] | false);
    if (tipo == "hola" && doc["datq"].is<int>()) ponAtraque(doc["datq"] | -1);
    if (tipo == "hola" && doc["noche"].is<bool>()) ponNoche(doc["noche"] | false);
    if (tipo == "foto") {
      ensenarFoto(doc["f"] | "", doc["port"] | 8081, doc["titulo"] | "", doc["dato"] | "", doc["seg"] | 6, doc["rot"] | false);
    } else if (tipo == "aviso") {
      if (finFoto) {                                // hay una foto: el aviso espera a que acabe
        pendEv = (const char*)(doc["ev"] | ""); pendKind = (const char*)(doc["kind"] | "");
        pendTit = (const char*)(doc["titulo"] | ""); pendDat = (const char*)(doc["dato"] | ""); pend = true;
      } else {
        reaccionar(doc["ev"] | "", doc["kind"] | "", doc["titulo"] | "", doc["dato"] | "");
      }
    }
  }
  if (panelVivo && t - tHola > 45000) {       // 45 s sin noticias del panel
    panelVivo = false; peligro = false; recarga = false; aPie = false; mapa = ""; ponColorCara(0);
    decir(Expression::Sleepy, "Panel apagado\n(o ROBOT desactivado)", "dormir", 8000);
    ponLuz(L_APAGADO, 0);
  }
}

void setup() {
  M5StackChan.begin();
  M5.Speaker.setVolume(90);
  brilloPantalla = M5.Display.getBrightness();
  M5StackChan.Motion.move(CX, CY, 300);
  M5StackChan.showRgbColor(0, 0, 0);

  avatar.init();
  avatar.setSpeechFont(&fonts::efontJA_12);         // v1.1.9: letra mas pequeña, que no se salga
  texto = String("StackChan ") + ROBOT_VER + "\nConectando WiFi...";
  pon();

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED) {
    for (int k = 0; k < 10; k++) { delay(50); scrollTexto(millis()); }
    if (millis() - t0 > 20000) {               // 20 s sin conectar: diagnostico en pantalla
      int n = WiFi.scanNetworks();
      bool visto = false;
      for (int i = 0; i < n; i++) if (WiFi.SSID(i) == WIFI_SSID) visto = true;
      int st = WiFi.status();
      texto = String("WiFi: ") + (visto ? "la veo, " : "NO la veo (2,4 GHz?)\n")
              + (st == WL_CONNECT_FAILED ? "clave mal?" : "estado " + String(st)) + "\nreintento...";
      pon();
      WiFi.disconnect(); delay(200);
      WiFi.begin(WIFI_SSID, WIFI_PASS);
      t0 = millis();
    }
  }
  udp.begin(UDP_PORT);
  texto = String("StackChan ") + ROBOT_VER + "\nEsperando al panel\n" + WiFi.localIP().toString();
  pon();
}

void loop() {
  M5StackChan.update();
  unsigned long t = millis();

  escuchar(t);

  motorCabeza(t);
  pintaLuz(t);

  // v1.1.9: tocar la pantalla (sin foto) = hacerle una pregunta
  if (!finFoto && panelVivo && t - tFotoFuera > 800 && M5.Touch.getDetail().wasClicked()) preguntar();
  if (vozBuf && !M5.Speaker.isPlaying()) { free(vozBuf); vozBuf = nullptr; }

  if (finFoto) {                                    // foto en pantalla
    if (t > finFoto || M5.Touch.getCount()) quitarFoto();   // se quita sola o tocando la pantalla
    delay(10);
    return;
  }
  avatar.setMouthOpenRatio(t < finHabla ? (sinf(t / 60.0f) + 1) / 2 : 0);
  scrollTexto(t);
  if (finTexto && t > finTexto) {
    finTexto = 0;
    if (peligro) { avatar.setExpression(Expression::Angry); texto = motivo; pon(); }
    else if (recarga) { avatar.setExpression(Expression::Happy); texto = recTxt; pon(); }
    else if (dormido) { avatar.setExpression(Expression::Sleepy); texto = "Zzz..."; pon(); }
    else if (mapa.length()) { avatar.setExpression(Expression::Doubt); texto = textoMapa(); pon(); }
    else { ponTexto(""); if (panelVivo) avatar.setExpression(Expression::Neutral); }
  }


  // v1.1.9: cuenta atras del atraque en el bocadillo; nervioso en el ultimo minuto
  if (finAtq && panelVivo) {
    if (t >= finAtq) finAtq = 0;
    else {
      long s = (finAtq - t + 999) / 1000;
      if (s <= 60 && avAtq == 0) { avAtq = 1; avatar.setExpression(Expression::Doubt); mover("temblar"); ponLuz(L_ALARMA, 3000); M5.Speaker.tone(1200, 120); }
      if (s <= 30 && avAtq == 1) { avAtq = 2; mover("aviso"); M5.Speaker.tone(1400, 120); }
      if (!peligro && !finTexto) {
        char b[24]; snprintf(b, sizeof(b), "ATRAQUE %ld:%02ld", s / 60, s % 60);
        ponTexto(b);
      }
    }
  }

  // v1.1.9: dormido: "Zzz" que va y viene de un lado a otro
  if (panelVivo && dormido && !finTexto) {
    static unsigned long tz = 0; static int fz = 0;
    if (t - tz > 450) {
      tz = t; fz = (fz + 1) % 10;
      const char* Z[] = {"Zzz", " zZz", "  zzZ", "   Zzz", "    zZz", "     zzZ", "    Zzz", "   zZz", "  zzZ", " Zzz"};
      ponTexto(Z[fz]);
    }
  }

  // v1.1.9: copiloto en ruta cuando no hay otra cosa que decir
  if (panelVivo && !dormido && !peligro && !recarga && !mapa.length() && !finTexto && !finAtq) {
    ponTexto(cop);
  }

  // si no pasa nada, de vez en cuando mira alrededor
  if (panelVivo && !dormido && !peligro && iPaso >= nPasos && t - tIdle > (mapa.length() ? 3000UL : 25000UL)) { tIdle = t; mover("mirar"); }

  // tocar la cabeza: repite el ultimo aviso (de los ultimos 15 min); si no hay, saluda (como mucho uno por minuto)
  if (M5StackChan.TouchSensor.wasPressed()) {
    if (ultTxt.length() && t - tUlt < 900000UL) {
      decir(Expression::Neutral, ultTxt, "asentir", 7000);
    } else if (t - tToque > 60000) {
      tToque = t;
      decir(Expression::Happy, "o7 Comandante", "asentir", 3000);
      ponLuz(L_BIEN, 2000);
    }
  }
  delay(10);
}
