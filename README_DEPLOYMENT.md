# 🚀 Kraken Trading Bot Deployment Guide

This guide will help you deploy your advanced Kraken trading bot to a production server.

## 📋 Prerequisites

### Server Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB+ (8GB+ recommended)
- **Storage**: 20GB+ available space
- **Network**: Stable internet connection

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Git

## 🛠️ Quick Deployment

### 1. Server Setup (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for Docker group to take effect
exit
# SSH back into your server
```

### 2. Clone and Deploy

```bash
# Clone the repository
git clone <your-repo-url>
cd kraken-trading-bot

# Run deployment script
./deploy.sh
```

### 3. Configure API Keys

```bash
# Edit the environment file
nano .env

# Add your Kraken API credentials:
KRAKEN_API_KEY=your_actual_api_key
KRAKEN_SECRET_KEY=your_actual_secret_key
KRAKEN_SANDBOX=false  # Set to false for live trading
```

### 4. Start the Bot

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f trading-bot
```

## 🌐 Access Points

After deployment, you can access:

- **Trading Bot Dashboard**: `http://your-server-ip`
- **Grafana Monitoring**: `http://your-server-ip/grafana` (admin/admin)
- **Prometheus Metrics**: `http://your-server-ip/prometheus`

## 🔧 Manual Deployment

If you prefer manual deployment:

### 1. Create Environment File

```bash
cp .env.example .env
# Edit .env with your settings
```

### 2. Build and Start

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

## 📊 Monitoring Setup

### Grafana Dashboards

1. Access Grafana at `http://your-server-ip/grafana`
2. Login with `admin/admin`
3. Import dashboards for:
   - Trading performance
   - Risk metrics
   - System monitoring

### Prometheus Metrics

The bot automatically exports metrics to Prometheus:
- Trade execution times
- Strategy performance
- Risk metrics
- System health

## 🔒 Security Considerations

### 1. Firewall Setup

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. SSL Certificate (Optional)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 3. API Key Security

- Store API keys in environment variables
- Use read-only API keys when possible
- Regularly rotate API keys
- Monitor API usage

## 🚨 Production Checklist

Before going live:

- [ ] Test in sandbox mode for at least 1 week
- [ ] Verify all risk management parameters
- [ ] Set up monitoring alerts
- [ ] Configure backup strategy
- [ ] Test disaster recovery
- [ ] Set up logging aggregation
- [ ] Configure rate limiting
- [ ] Set up automated backups

## 📈 Scaling Options

### Vertical Scaling
```bash
# Increase container resources in docker-compose.yml
services:
  trading-bot:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### Horizontal Scaling
```bash
# Run multiple bot instances
docker-compose up -d --scale trading-bot=3
```

## 🔄 Maintenance

### Regular Tasks

```bash
# Update bot
git pull
docker-compose build
docker-compose up -d

# Backup database
docker-compose exec postgres pg_dump -U postgres kraken_bot > backup.sql

# View logs
docker-compose logs -f trading-bot

# Restart services
docker-compose restart
```

### Monitoring Commands

```bash
# Check service status
docker-compose ps

# Monitor resource usage
docker stats

# Check disk space
df -h

# Monitor logs
tail -f logs/trading_bot.log
```

## 🆘 Troubleshooting

### Common Issues

1. **Bot not starting**
   ```bash
   docker-compose logs trading-bot
   # Check API keys and network connectivity
   ```

2. **Database connection issues**
   ```bash
   docker-compose exec postgres psql -U postgres -d kraken_bot
   # Check database status
   ```

3. **High memory usage**
   ```bash
   docker stats
   # Consider increasing memory limits
   ```

4. **API rate limiting**
   ```bash
   # Check logs for rate limit errors
   docker-compose logs trading-bot | grep "rate limit"
   ```

### Emergency Stop

```bash
# Stop all trading immediately
docker-compose down

# Or stop just the trading bot
docker-compose stop trading-bot
```

## 📞 Support

For issues:
1. Check logs: `docker-compose logs trading-bot`
2. Verify configuration in `.env`
3. Test API connectivity
4. Check system resources

## 🔄 Updates

To update the bot:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify deployment
docker-compose ps
```

## 📊 Performance Optimization

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_trades_symbol_timestamp ON trades(symbol, timestamp);
CREATE INDEX CONCURRENTLY idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
```

### Memory Optimization

```yaml
# In docker-compose.yml
services:
  trading-bot:
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    deploy:
      resources:
        limits:
          memory: 2G
```

## 🎯 Best Practices

1. **Start Small**: Begin with small position sizes
2. **Monitor Constantly**: Check performance daily
3. **Backup Regularly**: Automated database backups
4. **Test Changes**: Always test in sandbox first
5. **Document Everything**: Keep deployment notes
6. **Security First**: Regular security updates
7. **Performance Monitoring**: Track key metrics
8. **Disaster Recovery**: Have backup plans ready

---

**⚠️ Important**: This bot trades with real money. Always test thoroughly in sandbox mode before going live. Monitor performance closely and be prepared to stop trading if needed.