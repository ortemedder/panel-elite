// StackChan (kit oficial M5Stack, CoreS3) para el Panel Elite
// CMDR ORTEM ED DER y Claude
// Recibe los avisos del panel v1.1.2+ por UDP 5007 (12 AJUSTES > ROBOT). No necesita EMITIR.
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
        r = BRILLO * k; g = BRILLO * k * 0.35f; break; }
      case L_ALARMA: {            // rojo parpadeando, alterna lados
        bool on = ((int)(e * 6) + (i < 6 ? 0 : 1)) % 2;
        r = on ? BRILLO : 0; break; }
      case L_SALTO: {             // azul que recorre la tira
        int pos = (int)(e * 14) % 6;
        int j = i < 6 ? i : 11 - i;
        float k = j == pos ? 1.0f : (abs(j - pos) == 1 ? 0.3f : 0.05f);
        r = BRILLO * k * 0.2f; g = BRILLO * k * 0.5f; b = BRILLO * k; break; }
      case L_BIEN: {              // verde que se apaga poco a poco
        float k = max(0.1f, 1.0f - e / 4.0f);
        g = BRILLO * k; b = BRILLO * k * 0.2f; break; }
      case L_RECARGA: {           // amarillo que se llena desde abajo
        int nivel = (int)(e * 4) % 7;
        int j = i < 6 ? i : 11 - i;
        float k = j < nivel ? 1.0f : 0.1f;
        r = BRILLO * k; g = BRILLO * k * 0.75f; break; }
      case L_TRISTE: {            // violeta tenue
        float k = 0.25f + 0.15f * sinf(e * 2.0f);
        r = BRILLO * k * 0.5f; b = BRILLO * k; break; }
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

void decir(Expression cara, const String& txt, const char* mov, unsigned long ms) {
  avatar.setExpression(cara);
  texto = txt.length() > 60 ? txt.substring(0, 60) : txt;
  avatar.setSpeechText(texto.c_str());
  mover(mov);
  unsigned long t = millis();
  finHabla = t + 1500; finTexto = t + ms; tIdle = t;
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

void ensenarFoto(const String& f, int port, String tit, String dat, int seg) {
  uint8_t* buf = nullptr; int len = 0;
  if (!bajarFoto(f, port, buf, len)) return;
  avatar.suspend();
  delay(60);
  auto& d = M5.Display;
  d.drawJpg(buf, len, 0, 0, 320, 240);
  free(buf);
  tit = sinTildes(tit); dat = sinTildes(dat);
  if (tit.length() || dat.length()) {                 // rotulo abajo, estilo panel
    int h = dat.length() ? 44 : 26;
    d.fillRect(0, 240 - h, 320, h, TFT_BLACK);
    d.drawFastHLine(0, 240 - h, 320, 0xFC60);
    d.setFont(&fonts::efontJA_16);
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
  finFoto = 0;
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
  const uint16_t fondos[] = {TFT_BLACK, 0xC000, 0xFE00, 0x2D84, 0x3B3F, 0xFC00};
  uint16_t fondo = fondos[constrain(c, 0, 5)];
  cp.set(COLOR_PRIMARY, c ? TFT_BLACK : TFT_WHITE);            // ojos y boca
  cp.set(COLOR_BACKGROUND, fondo);
  cp.set(COLOR_BALLOON_FOREGROUND, TFT_BLACK);
  cp.set(COLOR_BALLOON_BACKGROUND, TFT_WHITE);
  avatar.setColorPalette(cp);
}


// color segun el estado (el peligro manda sobre todo)
int colorBase() {
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
    texto = motivo; avatar.setSpeechText(texto.c_str());
    ponLuz(L_ALARMA, 0);
    if (empieza) { mover("aviso"); M5.Speaker.tone(1200, 150); }    // un solo gesto corto al empezar
    finTexto = 0;
  } else if (recarga) {
    avatar.setExpression(Expression::Happy);
    texto = recTxt; avatar.setSpeechText(texto.c_str()); finTexto = 0;
    ponLuz(L_RECARGA, 0);
  } else {
    avatar.setExpression(Expression::Happy);
    texto = "Peligro superado"; avatar.setSpeechText(texto.c_str());
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
    texto = recTxt; avatar.setSpeechText(texto.c_str()); finTexto = 0;
    ponLuz(L_RECARGA, 0);
    if (empieza) M5.Speaker.tone(2000, 60);
  } else {
    avatar.setExpression(Expression::Neutral); avatar.setSpeechText(""); finTexto = 0;
    ponLuz(L_BIEN, 2000);
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
        avatar.setExpression(Expression::Neutral); avatar.setSpeechText(""); finTexto = 0;
        ponLuz(L_REPOSO, 0); M5StackChan.Motion.move(CX, CY, 300);
      }
    }
    String tipo = doc["t"] | "";
    if (tipo == "peligro" || tipo == "hola") {
      if (tipo == "peligro" || doc["peligro"].is<bool>()) ponPeligro(doc[tipo == "peligro" ? "on" : "peligro"] | false, doc["motivo"] | "");
      if (doc["recarga"].is<bool>()) ponRecarga(doc["recarga"] | false, doc["rectxt"] | "");
      if (doc["pie"].is<bool>()) ponPie(doc["pie"] | false, doc["clima"] | "");
    }
    if (tipo == "foto") {
      ensenarFoto(doc["f"] | "", doc["port"] | 8081, doc["titulo"] | "", doc["dato"] | "", doc["seg"] | 6);
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
    panelVivo = false; peligro = false; recarga = false; aPie = false; ponColorCara(0);
    decir(Expression::Sleepy, "Panel apagado\n(o ROBOT desactivado)", "dormir", 8000);
    ponLuz(L_APAGADO, 0);
  }
}

void setup() {
  M5StackChan.begin();
  M5.Speaker.setVolume(90);
  M5StackChan.Motion.move(CX, CY, 300);
  M5StackChan.showRgbColor(0, 0, 0);

  avatar.init();
  avatar.setSpeechFont(&fonts::efontJA_16);
  texto = "Conectando WiFi...";
  avatar.setSpeechText(texto.c_str());

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    if (millis() - t0 > 20000) {               // 20 s sin conectar: diagnostico en pantalla
      int n = WiFi.scanNetworks();
      bool visto = false;
      for (int i = 0; i < n; i++) if (WiFi.SSID(i) == WIFI_SSID) visto = true;
      int st = WiFi.status();
      texto = String("WiFi: ") + (visto ? "la veo, " : "NO la veo (2,4 GHz?)\n")
              + (st == WL_CONNECT_FAILED ? "clave mal?" : "estado " + String(st)) + "\nreintento...";
      avatar.setSpeechText(texto.c_str());
      WiFi.disconnect(); delay(200);
      WiFi.begin(WIFI_SSID, WIFI_PASS);
      t0 = millis();
    }
  }
  udp.begin(UDP_PORT);
  texto = "Esperando al panel\n" + WiFi.localIP().toString();
  avatar.setSpeechText(texto.c_str());
}

void loop() {
  M5StackChan.update();
  unsigned long t = millis();

  escuchar(t);

  motorCabeza(t);
  pintaLuz(t);

  if (finFoto) {                                    // foto en pantalla
    if (t > finFoto || M5.Touch.getCount()) quitarFoto();   // se quita sola o tocando la pantalla
    delay(10);
    return;
  }
  avatar.setMouthOpenRatio(t < finHabla ? (sinf(t / 60.0f) + 1) / 2 : 0);
  if (finTexto && t > finTexto) {
    finTexto = 0;
    if (peligro) { avatar.setExpression(Expression::Angry); texto = motivo; avatar.setSpeechText(texto.c_str()); }
    else if (recarga) { avatar.setExpression(Expression::Happy); texto = recTxt; avatar.setSpeechText(texto.c_str()); }
    else { avatar.setSpeechText(""); if (panelVivo) avatar.setExpression(Expression::Neutral); }
  }


  // si no pasa nada, de vez en cuando mira alrededor
  if (panelVivo && !peligro && iPaso >= nPasos && t - tIdle > 25000) { tIdle = t; mover("mirar"); }

  // tocar la cabeza = saludo
  if (M5StackChan.TouchSensor.wasPressed() && t - tToque > 60000) {   // como mucho un saludo por minuto
    tToque = t;
    decir(Expression::Happy, "o7 Comandante", "asentir", 3000);
    ponLuz(L_BIEN, 2000);
  }
  delay(10);
}
