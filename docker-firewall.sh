#!/usr/bin/env bash
set -euo pipefail

MODE=install
if [[ "${1:-}" == --apply ]]; then
  MODE=apply
  shift
fi
if [[ "$EUID" -ne 0 || "$#" -lt 2 || "$#" -gt 3 ]]; then
  echo "Usage: sudo bash docker-firewall.sh HOST_IPV4 TRUSTED_IPV4_CIDR [PORT]"
  exit 1
fi
HOST_IP="$1"
TRUSTED_SUBNET="$2"
PORT="${3:-8000}"
IPV4_PATTERN='[0-9]{1,3}(\.[0-9]{1,3}){3}'
if [[ ! "$HOST_IP" =~ ^$IPV4_PATTERN$ || "$HOST_IP" == 0.0.0.0 \
  || ! "$TRUSTED_SUBNET" =~ ^$IPV4_PATTERN/[0-9]{1,2}$ \
  || ! "$PORT" =~ ^[0-9]{1,5}$ ]]; then
  echo "Error: use a specific host IPv4 address, a trusted IPv4 CIDR, and a numeric port."
  exit 1
fi
PORT=$((10#$PORT))
if (( PORT < 1 || PORT > 65535 )); then
  echo "Error: port must be between 1 and 65535."
  exit 1
fi

if [[ "$MODE" == install ]]; then
  if ! iptables -w -n -L DOCKER-USER >/dev/null; then
    echo "Error: start Docker with its iptables firewall backend before configuring LAN access."
    exit 1
  fi
else
  if ! iptables -w -n -L DOCKER-USER >/dev/null 2>&1; then
    iptables -w -N DOCKER-USER
  fi
fi

# Replace only this app's chain in one transaction, without flushing other rules.
iptables-restore --wait 10 --noflush <<EOF
*filter
:LLM-LECTURE - [0:0]
-A LLM-LECTURE -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
-A LLM-LECTURE -s $TRUSTED_SUBNET -j RETURN
-A LLM-LECTURE -j DROP
COMMIT
EOF

MATCH=(-p tcp -m conntrack --ctdir ORIGINAL --ctorigdst "$HOST_IP" --ctorigdstport "$PORT" -j LLM-LECTURE)
if ! iptables -w -C DOCKER-USER "${MATCH[@]}" 2>/dev/null; then
  iptables -w -I DOCKER-USER 1 "${MATCH[@]}"
fi

if [[ "$MODE" == apply ]]; then
  exit 0
fi

install -m 0755 "${BASH_SOURCE[0]}" /usr/local/sbin/llm-lecture-firewall
install -d -m 0755 /etc/systemd/system/docker.service.d
cat > /etc/llm-lecture-firewall.conf <<EOF
HOST_IP=$HOST_IP
TRUSTED_SUBNET=$TRUSTED_SUBNET
PORT=$PORT
EOF
chmod 0644 /etc/llm-lecture-firewall.conf
cat > /etc/systemd/system/llm-lecture-firewall.service <<'EOF'
[Unit]
Description=Restrict LLM Lecture Docker LAN access
Before=docker.service

[Service]
Type=oneshot
EnvironmentFile=/etc/llm-lecture-firewall.conf
ExecStart=/usr/local/sbin/llm-lecture-firewall --apply ${HOST_IP} ${TRUSTED_SUBNET} ${PORT}
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/docker.service.d/llm-lecture-firewall.conf <<'EOF'
[Unit]
Requires=llm-lecture-firewall.service
After=llm-lecture-firewall.service
EOF
systemctl daemon-reload
systemctl enable --now llm-lecture-firewall.service
echo "Docker port $HOST_IP:$PORT allows $TRUSTED_SUBNET only."
