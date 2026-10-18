# Lexman ENKI / ADEO WSD005 con Home Assistant (ZHA)

**Guía para usar un motor de persiana Lexman Zigbee directamente con Home Assistant y ZHA, sin comprar la central Enki.** Se puede conservar el mando original de **433 MHz** y, si hace falta, corregir la posición invertida mediante un quirk opcional.

[English README](README.md) · [Instalación técnica (EN)](docs/installation.md) · [Solución de problemas (EN)](docs/troubleshooting.md) · [Detalles del quirk (EN)](docs/technical-details.md)

> **Probado en una instalación real, no es una integración oficial.** El dispositivo Zigbee comprobado se identifica como fabricante `Adeo`, modelo `WSD005`. La ficha del producto Lexman 87554450 corresponde a un motor de 10 Nm para eje de 40 mm. No extrapoles los resultados a cualquier motor Lexman ni a todos sus firmwares.

## ¿Qué se ha comprobado?

| Función | Resultado |
| --- | --- |
| Emparejamiento directo con ZHA, sin central Enki | ✅ Comprobado |
| Mando de 433 MHz y Zigbee simultáneamente | ✅ Comprobado |
| Apertura y cierre desde Home Assistant | ✅ Comprobado |
| Finales de carrera configurados con el mando | ✅ Comprobado |
| Posición intermedia del 50 % | ✅ Comprobado |
| Estado cerrado = 0 % mediante el quirk | ✅ Comprobado en el motor afectado |
| Función STOP de ZHA por separado | No hay una prueba física específica documentada |
| Otros modelos y otras versiones de firmware | No comprobados |

La documentación de Lexman exige una central Enki **para utilizar la aplicación Enki**. Eso no impide que **este dispositivo concreto** se haya conectado directamente a ZHA con un coordinador Zigbee compatible.

## Instalación rápida

1. **Instala el motor según su manual**, con el circuito eléctrico desconectado. Funciona con tensión de red; si no tienes competencia para realizar el trabajo eléctrico, encárgaselo a un profesional. Comprueba que soporte, adaptadores, eje y fijaciones de la persiana sean los adecuados.
2. **Empareja el mando de 433 MHz:** selecciona el canal, pulsa una vez el botón del **cabezal del motor** y después una vez el pequeño **botón de emparejamiento del mando**. El motor debe confirmar con un movimiento breve. Consulta el [manual, página 29 en español](https://www.manualslib.es/manual/913385/Lexman-87554450.html?page=29).
3. **Configura los dos finales de carrera con el mando**, comprobando que el botón de subir realmente sube y que el de bajar baja. En el modelo documentado, coloca la persiana en el límite inferior y pulsa dos veces el botón de emparejamiento del mando seguido de bajar; para el superior, repite el proceso en el extremo alto con la flecha de subir. El motor confirma con un movimiento breve. Detente si hay resistencia o si el sentido es incorrecto.
4. **Empareja Zigbee en ZHA:** abre **Ajustes → Dispositivos y servicios → ZHA → Añadir dispositivo**. Si hace falta poner el módulo en modo emparejamiento, la documentación de Enki indica **cuatro pulsaciones rápidas (menos de 1,5 segundos)** sobre el **botón central del módulo Zigbee**, no el botón del cabezal. Su LED debe parpadear en azul. **Atención: esto reinicia el módulo Zigbee**; no lo hagas si ya está conectado y funcionando.
5. **Comprueba la posición indicada en Home Assistant**, antes de activar automatizaciones. Si aparece completamente abierta cuando está físicamente cerrada, lee primero el valor original del dispositivo como se explica abajo.
6. **Si se confirma la inversión**, instala el quirk opcional y verifica el porcentaje por lectura antes de hacer una prueba de movimiento supervisada.

No actives sin más el interruptor `Inverted` de ZHA: puede alterar el sentido del motor y no es equivalente a invertir solamente el porcentaje mostrado.

## ¿Qué problema corrige el quirk?

En nuestro motor, una lectura directa del atributo `0x0008` del clúster `0x0102` (Window Covering), endpoint `1`, dio:

| Estado físico | Valor Zigbee | ZHA sin corregir | ZHA con quirk |
| --- | --- | --- | --- |
| Persiana cerrada | `0` | 100 % abierta | 0 % (cerrada) |
| Abierta un poco | `5` | 95 % abierta | 5 % abierta |

ZHA interpretaba el porcentaje al revés. El archivo [`adeo_wsd005_position.py`](adeo_wsd005_position.py) modifica **solo la interpretación en ZHA**, sin cambiar los finales de carrera, la dirección del motor ni las órdenes enviadas.

### Instalar la corrección (solo si tienes este síntoma)

1. En Home Assistant, verifica la posición real del motor y consulta mediante **Administrar dispositivo Zigbee** el atributo `0x0008` del clúster `0x0102`. Las lecturas no mueven la persiana.
2. Descarga el archivo [`adeo_wsd005_position.py`](adeo_wsd005_position.py) y cópialo a `/config/custom_zha_quirks/adeo_wsd005_position.py`.
3. En tu **copia instalada**, sustituye `TARGET_IEEE: str | None = None` por tu propia dirección IEEE permanente (por ejemplo, `TARGET_IEEE: str | None = "aa:bb:cc:dd:ee:ff:00:11"`). El IEEE del ejemplo es ficticio. **No uses la dirección NWK temporal**. Mantén privada tu copia personalizada.
4. Añade el directorio a `configuration.yaml` (integra la opción en el bloque `zha:` existente si lo hay):

   ```yaml
   zha:
     custom_quirks_path: /config/custom_zha_quirks
   ```

5. Haz copia de seguridad, valida la configuración y revisa si tienes automatizaciones que puedan mover persianas al reiniciar. Reinicia Home Assistant cuando sea seguro hacerlo.
6. Comprueba que ZHA indica `quirk_applied: true` y que, con valor Zigbee original `0`, Home Assistant indica **cerrada al 0 %**. No hace falta mover la persiana para esta comprobación.
7. Después, **comprueba por separado** apertura, cierre y posiciones intermedias, siempre con supervisión presencial y posibilidad de cortar la alimentación. El quirk no cambia las órdenes de movimiento.

Para más detalles de instalación, incompatibilidades, pruebas y reversión, consulta [docs/technical-details.md](docs/technical-details.md).

## Zigbee2MQTT

[Zigbee2MQTT documenta el WSD005](https://www.zigbee2mqtt.io/devices/WSD005.html) y ofrece la opción `invert_cover`. Esta solución en Python es **exclusiva de ZHA** y no debe instalarse en Zigbee2MQTT.

## Fuentes, colaboración y seguridad

- [Ficha técnica oficial de Enki (español)](https://support.enki-home.com/hc/es-es/articles/20527012703890-Lexman-Motor-conectado-de-sustituci%C3%B3n-para-persiana-enrollable-Ficha-del-producto)
- [Manual Lexman 87554450](https://www.manualslib.es/manual/913385/Lexman-87554450.html)
- [Documentación de ZHA](https://www.home-assistant.io/integrations/zha/)
- [Abrir una incidencia / issue](https://github.com/Cachaza/adeo-wsd005-zha-position-fix/issues)

Si tienes otro firmware o comportamiento, comparte la versión y lecturas originales con sus posiciones físicas, pero **no publiques tu IEEE, claves Zigbee, tokens ni diagnósticos privados sin anonimizar**.

Proyecto comunitario independiente de ADEO, Lexman, Home Assistant y zigpy. Licencia [MIT](LICENSE).
