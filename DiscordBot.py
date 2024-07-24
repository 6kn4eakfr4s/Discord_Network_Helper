from scapy.all import *
import discord
from discord import app_commands
import dns.exception
import requests
import json
import dns.resolver
from ipwhois import IPWhois
import speedtest

IPv4API = "https://api.ipify.org"

config = open("config.json", "r").read()
config_json = json.loads(config)
TOKEN = config_json["DiscordToken"]


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# dns query
def SpeedTest():
  s = speedtest.Speedtest()
  s.get_closest_servers()
  s.get_best_server()
  s.download()
  s.upload()
  s.results.share()
  result_url = list(s.results.dict()["share"])
  result_url.insert(4, "s")
  return "".join(result_url)[0:-4]


def DNSQuery(domain, query_type):
  resolver = dns.resolver.Resolver()
  resolver.nameservers = ["8.8.8.8"]
  try:
    result_message = resolver.resolve(domain, query_type)
    result = result_message.rrset.to_text()
  except dns.resolver.NXDOMAIN:
    result = "Non-existing domain!"
  except dns.resolver.NoAnswer:
    result = "No records!"
  except dns.exception.Timeout:
    result = "Time out!"
  except dns.resolver.LifetimeTimeout:
    result = "Lifetime timeout!"
  except Exception as e:
      result = e
  return result


def Traceroute(destination, max_hops=30):
  result = []
  for ttl in range(1, max_hops + 1):
    pkt = IP(dst=destination, ttl=ttl) / ICMP()

    reply = sr1(pkt, verbose=0, timeout=2)

    if reply is None:
      result.append(f"{ttl}: Request timed out")
      continue

    latency = (reply.time - pkt.sent_time) * 1000  # Convert to milliseconds

    try:
      hostname = socket.gethostbyaddr(reply.src)[0]
    except socket.herror:
      hostname = "Hostname not found"

    try:
      ipwhois = IPWhois(reply.src)
      asn_info = ipwhois.lookup_rdap()
      asn = asn_info["asn"]
      asn_org = asn_info["asn_description"]
    except Exception as e:
      asn = "ASN not found"
      asn_org = str(e)

    if reply.type == 0:  # ICMP echo-reply
      result.append(
        f"{ttl}: {reply.src} ({hostname}), ASN: {asn} ({asn_org}), Latency: {latency:.2f} ms (Reached destination)"
      )
      break
    else:
      result.append(
        f"{ttl}: {reply.src} ({hostname}), ASN: {asn} ({asn_org}), Latency: {latency:.2f} ms"
      )

  return "\n".join(result)


@tree.command(name="current_ip", description="print current public IP")
async def current_ip(ctx):
  currentIPv4 = requests.get(IPv4API).text
  await ctx.response.send_message("Current ipv4: " + currentIPv4)


@tree.command(name="speedtest", description="do a speedtest with speedtest-cli")
async def spdtest(ctx):
  await ctx.response.send_message("Testing")
  await ctx.edit_original_response(content=SpeedTest())


@tree.command(name="dns_query", description="query a domain's DNS record")
async def dns_query(ctx, domain: str, query_type: str):
  result = DNSQuery(domain, query_type)
  await ctx.response.send_message(result)

@tree.command(name="traceroutev4", description="do a traceroute to an IPv4 address")
async def traceroutev4(ctx, destination: str):
  await ctx.response.send_message("Tracerouting")
  await ctx.edit_original_response(content=Traceroute(destination))

@client.event
async def on_ready():
  await tree.sync()
  print("ready")


client.run(TOKEN)
