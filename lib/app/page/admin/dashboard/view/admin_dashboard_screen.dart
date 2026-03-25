import 'package:aura/app/theme/text_style/app_text_style.dart';
import 'package:flutter/material.dart';

import 'package:fl_chart/fl_chart.dart';
import '../../../../theme/color/color.dart';

class AdminDashboardScreen extends StatelessWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.menu,
                    color: ColorResources.whiteColor,
                    size: 22,
                  ),
                  const Expanded(
                    child: Text(
                      'DASHBOARD',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 4.0,
                      ),
                    ),
                  ),
                  const Icon(
                    Icons.notifications_outlined,
                    color: ColorResources.whiteColor,
                    size: 22,
                  ),
                  const SizedBox(width: 12),
                  CircleAvatar(
                    radius: 18,
                    backgroundColor: ColorResources.cardColor,
                    backgroundImage: const AssetImage(
                      'assets/images/profile.jpg',
                    ),
                    onBackgroundImageError: (_, __) {},
                    child: const Icon(
                      Icons.person,
                      color: ColorResources.whiteColor,
                      size: 18,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 28),

              // Stats Grid
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.3,
                children: const [
                  _StatCard(
                    label: 'TODAY\nREVENUE',
                    value: '\$1,240',
                    change: '+5.2%',
                    isPositive: true,
                  ),
                  _StatCard(
                    label: 'WEEKLY\nREVENUE',
                    value: '\$8,900',
                    change: '+1.8%',
                    isPositive: true,
                  ),
                  _StatCard(
                    label: 'MONTHLY\nREVENUE',
                    value: '\$34,200',
                    change: '+12.4%',
                    isPositive: true,
                  ),
                  _StatCard(
                    label: 'TODAY\nAPPOINTMENTS',
                    value: '12',
                    change: '-2%',
                    isPositive: false,
                  ),
                ],
              ),

              const SizedBox(height: 20),

              // Revenue Trend Chart
              _RevenueTrendCard(),

              const SizedBox(height: 20),

              // Best Selling Services
              _BestSellingServices(),

              const SizedBox(height: 20),

              // Therapist Performance
              _TherapistPerformance(),

              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}

// ── STAT CARD ──────────────────────────────────────────────
class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final String change;
  final bool isPositive;

  const _StatCard({
    required this.label,
    required this.value,
    required this.change,
    required this.isPositive,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppTextStyles.headingSmall.copyWith(fontSize: 10)),

          Text(
            value,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 26,
              fontWeight: FontWeight.w300,
              letterSpacing: 0.5,
            ),
          ),
          SizedBox(height: 8),
          Row(
            children: [
              Icon(
                isPositive ? Icons.trending_up : Icons.trending_down,
                color: isPositive
                    ? ColorResources.positiveColor
                    : ColorResources.negativeColor,
                size: 13,
              ),
              const SizedBox(width: 4),
              Text(
                change,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: isPositive
                      ? ColorResources.positiveColor
                      : ColorResources.negativeColor,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── REVENUE TREND CHART ────────────────────────────────────
class _RevenueTrendCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('REVENUE TREND', style: AppTextStyles.headingSmall),
          const SizedBox(height: 8),
          Row(
            children: [
              const Text(
                '\$34,200',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 28,
                  fontWeight: FontWeight.w300,
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(width: 10),
              Text(
                'Total Growth',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.liteTextColor,
                  fontSize: 13,
                  fontWeight: FontWeight.w300,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'LAST 30 DAYS',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor,
              fontSize: 10,

              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 20),
          SizedBox(
            height: 160,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (_) => FlLine(
                    color: ColorResources.whiteColor.withOpacity(0.06),
                    strokeWidth: 0.5,
                  ),
                ),
                titlesData: FlTitlesData(
                  leftTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, _) {
                        const weeks = [
                          'WEEK 01',
                          'WEEK 02',
                          'WEEK 03',
                          'WEEK 04',
                        ];
                        if (value.toInt() >= 0 &&
                            value.toInt() < weeks.length) {
                          return Text(
                            weeks[value.toInt()],
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.liteTextColor,
                              fontSize: 8,
                              letterSpacing: 1.0,
                            ),
                          );
                        }
                        return const SizedBox();
                      },
                      reservedSize: 24,
                      interval: 1,
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                lineBarsData: [
                  LineChartBarData(
                    spots: const [
                      FlSpot(0, 2),
                      FlSpot(0.3, 5),
                      FlSpot(0.6, 3),
                      FlSpot(0.9, 6),
                      FlSpot(1.2, 4),
                      FlSpot(1.5, 7),
                      FlSpot(1.8, 5),
                      FlSpot(2.1, 9),
                      FlSpot(2.4, 6),
                      FlSpot(2.7, 8),
                      FlSpot(3.0, 5),
                      FlSpot(3.3, 7),
                      FlSpot(3.6, 4),
                      FlSpot(3.9, 6),
                    ],
                    isCurved: true,
                    color: ColorResources.primaryColor,
                    barWidth: 1.5,
                    isStrokeCapRound: true,
                    dotData: const FlDotData(show: false),
                    belowBarData: BarAreaData(
                      show: true,
                      gradient: LinearGradient(
                        colors: [
                          ColorResources.primaryColor.withOpacity(0.15),
                          ColorResources.primaryColor.withOpacity(0.0),
                        ],
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                      ),
                    ),
                  ),
                ],
                minX: 0,
                maxX: 3.9,
                minY: 0,
                maxY: 10,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── BEST SELLING SERVICES ──────────────────────────────────
class _BestSellingServices extends StatelessWidget {
  final List<Map<String, dynamic>> services = const [
    {
      'icon': Icons.spa_outlined,
      'name': 'Deep Tissue\nMassage',
      'duration': '60 MINS',
      'price': '\$180',
      'bookings': '24\nBOOKINGS',
    },
    {
      'icon': Icons.face_retouching_natural_outlined,
      'name': 'Hydro-Facial\nTreatment',
      'duration': '45 MINS',
      'price': '\$220',
      'bookings': '62\nBOOKINGS',
    },
    {
      'icon': Icons.local_florist_outlined,
      'name': 'Swedish\nAromatherapy',
      'duration': '90 MINS',
      'price': '\$150',
      'bookings': '18\nBOOKINGS',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('BEST - SELLING SERVICES', style: AppTextStyles.headingSmall),
          const SizedBox(height: 20),
          ...services.map((s) => _ServiceRow(service: s)),
        ],
      ),
    );
  }
}

class _ServiceRow extends StatelessWidget {
  final Map<String, dynamic> service;
  const _ServiceRow({required this.service});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: ColorResources.primaryColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: ColorResources.primaryColor.withOpacity(0.3),
                width: 0.5,
              ),
            ),
            child: Icon(
              service['icon'] as IconData,
              color: ColorResources.primaryColor,
              size: 20,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  service['name'],
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 15,
                    fontWeight: FontWeight.w400,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  service['duration'],
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor.withOpacity(0.4),
                    fontSize: 10,
                    letterSpacing: 1.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                service['price'],
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 18,
                  fontWeight: FontWeight.w400,
                  letterSpacing: 0.5,
                ),
              ),
              Text(
                service['bookings'],
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor.withOpacity(0.4),
                  fontSize: 10,
                  letterSpacing: 1.5,
                  fontWeight: FontWeight.w600,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── THERAPIST PERFORMANCE ──────────────────────────────────
class _TherapistPerformance extends StatelessWidget {
  final List<Map<String, dynamic>> therapists = const [
    {
      'name': 'Elena\nRodriguez',
      'role': 'SENIOR THERAPIST',
      'rating': '4.9',
      'sessions': '44\nSESSIONS',
      'image':
          'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
    },
    {
      'name': 'Marcus Chen',
      'role': 'MASSAGE SPECIALIST',
      'rating': '4.8',
      'sessions': '38\nSESSIONS',
      'image':
          'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
    },
    {
      'name': 'Sarah Jenkins',
      'role': 'ESTHETICIAN',
      'rating': '5.0',
      'sessions': '51\nSESSIONS',
      'image':
          'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('THERAPIST PERFORMANCE', style: AppTextStyles.headingSmall),
          const SizedBox(height: 20),
          ...therapists.map((t) => _TherapistRow(therapist: t)),
        ],
      ),
    );
  }
}

class _TherapistRow extends StatelessWidget {
  final Map<String, dynamic> therapist;
  const _TherapistRow({required this.therapist});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Row(
        children: [
          CircleAvatar(
            radius: 26,
            backgroundColor: ColorResources.borderColor,
            backgroundImage: NetworkImage(therapist['image']),
            onBackgroundImageError: (_, __) {},
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  therapist['name'],
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w400,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  therapist['role'],
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor.withOpacity(0.4),
                    fontSize: 10,
                    letterSpacing: 1.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.star,
                    color: ColorResources.primaryColor,
                    size: 18,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    therapist['rating'],
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 15,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ],
              ),
              Text(
                therapist['sessions'],
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor.withOpacity(0.4),
                  fontSize: 10,
                  letterSpacing: 1.5,
                  fontWeight: FontWeight.w600,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
