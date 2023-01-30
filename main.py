import discord
from discord.ext import commands
import youtube_dl
from datetime import timedelta
import os


bot = commands.Bot(activity=discord.Game(name='24/7 Chill Lofi Music'), command_prefix='/', intents=discord.Intents.all())
bot.remove_command('help')


def human_format(num):
	num = float('{:.3g}'.format(num))
	magnitude = 0
	while abs(num) >= 1000:
		magnitude += 1
		num /= 1000.0
	return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


@bot.event
async def on_ready():
	print(f"---<= Logged In As: {bot.user} =>---")
	await bot.tree.sync()


@bot.tree.command(name="connect", description="(Owner Only) Connects the bot to the voice channel the author of the command is in.")
@commands.is_owner()
async def connect(interaction: discord.Interaction):
	if interaction.user.voice is None:
		embed = discord.Embed(
			title="⚠ Could Not Connect ⚠",
			description="Please join a voice channel before running this command!",
			color=discord.Colour.red()
		)
		await interaction.response.send_message(embed=embed)
	else:
		embed = discord.Embed(
			title="✅ Successfully Connected ✅",
			description=f"Connected To: `🔊 {interaction.user.voice.channel.name}`",
			color=discord.Colour.green()
		)
		await interaction.response.send_message(embed=embed)

		voice_channel = interaction.user.voice.channel
		if len(bot.voice_clients) == 0:
			await voice_channel.connect()
		else:
			await bot.voice_clients[0].move_to(voice_channel)


@bot.tree.command(name="play", description="(Owner Only) Plays audio from the specified YouTube video. Check `/help` for more details.")
@commands.is_owner()
async def play(interaction: discord.Interaction, loop: int, url: str):
	audio_stream = bot.voice_clients[0] if len(bot.voice_clients) != 0 else None
	if audio_stream is not None:
		audio_stream.stop()
		FFMPEG_OPTIONS = {
			'before_options': f'-stream_loop {-1 if int(loop) else 0} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
			'options': '-vn'
		}
		YDL_OPTIONS = {'format': 'bestaudio'}

		main_info = {
			'title': None,
			'audio_url': None,
			'yt_video_url': None,
			'duration': None,
			'view_count': None,
			'thumbnail': None,
		}

		with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
			info = ydl.extract_info(url, download=False)
			
			main_info['title'] = info['title']
			main_info['audio_url'] = info['formats'][0]['url']
			main_info['yt_video_url'] = info['webpage_url']
			main_info['duration'] = info['duration']
			main_info['view_count'] = info['view_count']
			main_info['thumbnail'] = info['thumbnail']

			source = await discord.FFmpegOpusAudio.from_probe(source=main_info['audio_url'], **FFMPEG_OPTIONS)
			audio_stream.play(source)

		embed = discord.Embed(
			title="🎵 Playing Music 🎵",
			description=f"Currently Playing: [{main_info['title']}]({main_info['yt_video_url']})\nLength: `{str(timedelta(seconds=main_info['duration']))}` | Views: `{human_format(main_info['view_count'])}` | Looping: `{'Yes' if int(loop) else 'No'}`",
			color=discord.Colour.green()
		)
		embed.set_image(url=main_info['thumbnail'])
		await interaction.response.send_message(embed=embed)
	else:
		embed = discord.Embed(
			title="⚠ Could Not Play Music ⚠",
			description=f"The bot is not currently connected to any voice channel. Please use the `/connect` command.",
			color=discord.Colour.red()
		)
		await interaction.response.send_message(embed=embed)


@bot.tree.command(name="pause", description="(Owner Only) Pauses the audio stream.")
@commands.is_owner()
async def pause(interaction: discord.Interaction):
	audio_stream = bot.voice_clients[0] if len(bot.voice_clients) != 0 else None
	if audio_stream is not None:
		if audio_stream.is_playing():
			audio_stream.pause()
			embed = discord.Embed(
				title="⏸ Audio Stream Paused ⏸",
				description=f"Music Has Been Paused In: `🔊 {audio_stream.channel.name}`",
				color=discord.Colour.yellow()
			)
			await interaction.response.send_message(embed=embed)
		elif audio_stream.is_paused():
			embed = discord.Embed(
				title="❗ Audio Stream Already Paused ❗",
				description=f"Music Has Already Been Paused In: `🔊 {audio_stream.channel.name}`",
				color=discord.Colour.yellow()
			)
			await interaction.response.send_message(embed=embed)
		else:
			embed = discord.Embed(
				title="⚠ Could Not Pause Audio Stream ⚠",
				description=f"There is no audio stream currently active.",
				color=discord.Colour.red()
			)
			await interaction.response.send_message(embed=embed)
	else:
		embed = discord.Embed(
			title="⚠ Could Not Pause Audio Stream ⚠",
			description=f"There is no audio stream currently active.",
			color=discord.Colour.red()
		)
		await interaction.response.send_message(embed=embed)


@bot.tree.command(name="resume", description="(Owner Only) Resumes the audio stream.")
@commands.is_owner()
async def resume(interaction: discord.Interaction):
	audio_stream = bot.voice_clients[0] if len(bot.voice_clients) != 0 else None
	if audio_stream is not None:
		if audio_stream.is_paused():
			embed = discord.Embed(
				title="▶ Audio Stream Resumed ▶",
				description=f"Music Has Been Resumed In: `🔊 {audio_stream.channel.name}`",
				color=discord.Colour.green()
			)
			await interaction.response.send_message(embed=embed)

			audio_stream.resume()
		elif audio_stream.is_playing():
			embed = discord.Embed(
				title="❗ Could Not Resume Audio Stream ❗",
				description=f"Audio Stream Was Not Paused. Music Continues To Play In: `🔊 {audio_stream.channel.name}`",
				color=discord.Colour.yellow()
			)
			await interaction.response.send_message(embed=embed)
		else:
			embed = discord.Embed(
				title="⚠ Could Not Resume Audio Stream ⚠",
				description=f"There is no audio stream currently active.",
				color=discord.Colour.red()
			)
			await interaction.response.send_message(embed=embed)
	else:
		embed = discord.Embed(
			title="⚠ Could Not Resume Audio Stream ⚠",
			description=f"There is no audio stream currently active.",
			color=discord.Colour.red()
		)
		await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stop", description="(Owner Only) Stops the audio stream.")
@commands.is_owner()
async def stop(interaction: discord.Interaction):
	audio_stream = bot.voice_clients[0] if len(bot.voice_clients) != 0 else None
	if audio_stream is not None:
		if audio_stream.is_playing() or audio_stream.is_paused():
			embed = discord.Embed(
				title="⏹ Audio Stream Stopped ⏹",
				description=f"Music Has Been Stopped In: `🔊 {audio_stream.channel.name}`",
				color=discord.Colour.red()
			)
			await interaction.response.send_message(embed=embed)

			audio_stream.stop()
		else:
			embed = discord.Embed(
				title="⚠ Could Not Stop Audio Stream ⚠",
				description=f"There is no audio stream currently active.",
				color=discord.Colour.red()
			)
			await interaction.response.send_message(embed=embed)
	else:
		embed = discord.Embed(
			title="⚠ Could Not Stop Audio Stream ⚠",
			description=f"There is no audio stream currently active.",
			color=discord.Colour.red()
		)
		await interaction.response.send_message(embed=embed)


@bot.tree.command(name="disconnect", description="(Owner Only) Disconnect the bot from the voice channel.")
@commands.is_owner()
async def disconnect(interaction: discord.Interaction):
	audio_stream = bot.voice_clients[0] if len(bot.voice_clients) != 0 else None
	if audio_stream is not None:
		embed = discord.Embed(
			title="✅ Successfully Disconnected ✅",
			description=f"Disconnected From: `🔊 {audio_stream.channel.name}`",
			color=discord.Colour.green()
		)
		await interaction.response.send_message(embed=embed)

		await audio_stream.disconnect()
	else:
		embed = discord.Embed(
			title="⚠ Could Not Disconnect ⚠",
			description=f"The bot is not currently connected to any voice chat.",
			color=discord.Colour.red()
		)
		await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ping", description="(Owner Only) Returns the average of most recent 20 HEARTBEAT latencies.")
@commands.is_owner()
async def ping(interaction: discord.Interaction):
	audio_stream = bot.voice_clients[0] if len(bot.voice_clients) != 0 else None
	if audio_stream is not None:
		embed = discord.Embed(
			title="❤ BeatBot's Heartbeat ❤",
			description=f"Bot Latency: `{round(audio_stream.average_latency, 3)*1000}ms`",
			color=discord.Colour.magenta()
		)
		await interaction.response.send_message(embed=embed)
	else:
		embed = discord.Embed(
			title="⚠ Could Not Check VC Ping ⚠",
			description=f"Please connect the bot to a voice channel first!",
			color=discord.Colour.red()
		)
		await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help", description="(Owner Only) Displays a list of commands for this bot.")
@commands.is_owner()
async def help(interaction: discord.Interaction):
	embed = discord.Embed(
		title="📜 List Of Commands 📜",
		color=discord.Colour.orange()
	)
	embed.add_field(name="/connect", value=f"Connects the bot to the voice channel the author of the command is in.", inline=False)
	embed.add_field(name="/play [0 or 1] [YouTube Video URL]", value=f"Plays audio from the specified YouTube video. Two arguments, first argument makes the stream loop (0 - off, 1 - on), second argument is the YouTube video URL.", inline=False)
	embed.add_field(name="/pause", value=f"Pauses the audio stream.", inline=False)
	embed.add_field(name="/resume", value=f"Resumes the audio stream.", inline=False)
	embed.add_field(name="/stop", value=f"Stops the audio stream.", inline=False)
	embed.add_field(name="/disconnect", value=f"Disconnects the bot from the voice channel.", inline=False)
	embed.add_field(name="/ping", value=f"Returns the average of most recent 20 HEARTBEAT latencies. Must be connected to voice channel for this command to work!", inline=False)
	embed.add_field(name="/help", value=f"Displays this list of commands.", inline=False)
	await interaction.response.send_message(embed=embed)


bot.run(os.getenv("BOT_TOKEN"))
