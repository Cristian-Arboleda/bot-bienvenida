import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import random
import os
import webserver

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# 1. Intents: Necesario para obtener nuevos miembros
intents = discord.Intents.default()
intents.members = True

# 2. Instancia del bot con prefijo (no obligatorio si solo usas eventos)
bot = commands.Bot(command_prefix='!', intents=intents)

# 3. Evento on_ready: confirma que el bot arrancó
@bot.event
async def on_ready():
    print(f"✅ conectado como {bot.user}") 

# 4. on_member_join: se invoca al entrar un nuevo miembro
@bot.event
async def on_member_join(member):
    # A) carga y prepara el fondo
    fondo_random = random.randint(1, 22)
    print(f'Fondo elegido: {fondo_random}')
    fondo = Image.open(f"img/fondo_{fondo_random}.jpg").convert("RGBA")
    fondo = fondo.rotate(90, expand=True)  # rota la imagen 90 grados
    
    # B) Descarga el avatar del usuario
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            avatar_bytes = await resp.read()
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    
    # Redimensiona el avatar al tamano que quieras (ej. 128x128 px)
    tamano_avatar = 300
    avatar = avatar.resize((tamano_avatar, tamano_avatar), Image.LANCZOS)
    
    # C) Aplica mascaras circular al avatar 
    mask = Image.new("L", (tamano_avatar, tamano_avatar), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0 , tamano_avatar, tamano_avatar), fill=255)
    avatar.putalpha(mask)
    
    # Ajusta (x, y) para posicionar
    avatar_x = fondo.width // 2 - tamano_avatar // 2
    avatar_y = fondo.height //2 - tamano_avatar // 2
    
    # Dibuja un borde alrededor del avatar
    borde_grosor = 10
    borde_radio = tamano_avatar + 2 * borde_grosor
    borde_x = avatar_x - borde_grosor
    borde_y = avatar_y - borde_grosor
    
    draw = ImageDraw.Draw(fondo)
    draw.ellipse(
        [borde_x, borde_y, borde_x + borde_radio, borde_y + borde_radio],
        outline=(173, 216, 230, 255), # AZUL
        width=borde_grosor
    )
    
    # Agregrar el nombre del servidor encima del avatar
    nombre_servidor = member.guild.name.upper()
    fuente_servidor = ImageFont.truetype("font/EXEPixelPerfect.ttf", size = 110)
    
    bbox_servidor = draw.textbbox((0, 0), nombre_servidor, font=fuente_servidor)
    width_servidor = bbox_servidor[2] - bbox_servidor[0]
    heigth_servidor = bbox_servidor[3] - bbox_servidor[1]
    text_x_servidor = fondo.width // 2
    text_y_servidor = avatar_y - heigth_servidor - 60 # 60px arriba del avatar
    
    # sombra
    sombra_offset = 5
    draw.text(
        (text_x_servidor - width_servidor // 2 + sombra_offset, text_y_servidor + sombra_offset),
        nombre_servidor, font=fuente_servidor, fill=(0, 0, 0, 255)
    )
    # texto principal
    draw.text(
        (text_x_servidor- width_servidor // 2, text_y_servidor),
        nombre_servidor, font=fuente_servidor, fill=(255, 182, 193, 255) # rosado
    )
    
    # D) Pega el avatar sobre el fondo
    pos_avatar = (avatar_x, avatar_y)
    fondo.paste(avatar, pos_avatar, avatar)
    
    draw = ImageDraw.Draw(fondo)
    # E) Escribe el nombre del usuario
    # carga fuente TTF
    try:
        fuente_nombre = ImageFont.truetype("font/EXEPixelPerfect.ttf", size=80)
        fuente_bienvenida = ImageFont.truetype("font/EXEPixelPerfect.ttf", size=100)
    except OSError:
        fuente_nombre = ImageFont.load_default(size=80)
        fuente_bienvenida = ImageFont.load_default(size=95)
    texto_nombre = f"{member.name}".upper()
    texto_bienvenida = "¡Bienvenid@!"
    # calcular el ancho del texto para centrarlo
    bbox_bienvenida =  draw.textbbox((0, 0), texto_bienvenida, font=fuente_bienvenida)
    width_bienvenida = bbox_bienvenida[2] - bbox_bienvenida[0]
    heigth_bienvenida = bbox_bienvenida[3] - bbox_bienvenida[1]
    
    bbox_nombre = draw.textbbox((0, 0), texto_nombre, font=fuente_nombre)
    width_nombre = bbox_nombre[2] - bbox_nombre[0]
    
    # posicion del texto: debajo del avatar,  uno debajo del otro
    text_x = fondo.width // 2
    text_y_bienvenida = avatar_y + tamano_avatar + 20 # debajo del avatar con un margen
    text_y_nombre = text_y_bienvenida + heigth_bienvenida + 20
    
    # Dibuja los textos centrados
    # Dibuja sombra negra
    sombra_offset = 5 # pixeles de desplazamiento para la sombra 
    # Bienvenida
    draw.text(
        (text_x - width_bienvenida // 2 + sombra_offset, text_y_bienvenida + sombra_offset), 
        texto_bienvenida, font=fuente_bienvenida, fill=(0, 0, 0, 255) # negro
    )
    # Nombre
    draw.text(
        (text_x - width_nombre // 2 + sombra_offset, text_y_nombre + sombra_offset), 
        texto_nombre, font=fuente_nombre, fill=(0, 0, 0, 255) # negro
    )
    # Dibuja texto encima
    draw.text(
        (text_x - width_bienvenida // 2, text_y_bienvenida),
        texto_bienvenida, font=fuente_bienvenida, fill=(255, 182, 193, 255) # rosado claro
    )
    draw.text(
        (text_x - width_nombre // 2, text_y_nombre),
        texto_nombre, font=fuente_nombre, fill=(173, 216, 230, 255) # azul claro
    )
    
    # F) envia la imagen al canal de bienvenida
    canal = discord.utils.get(member.guild.text_channels, name="bienvenida👋")
    if canal:
        with io.BytesIO() as output:
            fondo.convert("RGB").save(output, format="JPEG")
            output.seek(0)
            await canal.send(
                content=f"""
🎉 !Bienvenid@ {member.mention} a **{member.guild.name}**!
Tu participación es muy importante para mantener viva y activa esta comunidad. 
¡Estamos felices de tenerte con nosotros!
                """,
                file=discord.File(fp=output, filename="welcome.jpg")
            )

webserver.keep_alive()
# Ejecutar el bot
bot.run(DISCORD_TOKEN)
