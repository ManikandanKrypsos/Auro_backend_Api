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

              // Rebooking & Cancellation (Pie Charts)
              const _RebookingCancellationSection(),

              const SizedBox(height: 20),

              // Lead Concentration
              const _LeadConcentrationSection(),

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

// ── REBOOKING & CANCELLATION SECTION ────────────────────────
class _RebookingCancellationSection extends StatelessWidget {
  const _RebookingCancellationSection();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _MetricPieCard(
            title: 'REBOOKING RATE',
            percentage: 68,
            activeColor: ColorResources.primaryColor,
            label: 'REBOOKED',
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _MetricPieCard(
            title: 'CANCELLATION',
            percentage: 12,
            activeColor: ColorResources.negativeColor,
            label: 'CANCELLED',
          ),
        ),
      ],
    );
  }
}

class _MetricPieCard extends StatelessWidget {
  final String title;
  final double percentage;
  final Color activeColor;
  final String label;

  const _MetricPieCard({
    required this.title,
    required this.percentage,
    required this.activeColor,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: AppTextStyles.headingSmall.copyWith(fontSize: 10)),
          const SizedBox(height: 20),
          Center(
            child: SizedBox(
              height: 100,
              width: 100,
              child: Stack(
                children: [
                  PieChart(
                    PieChartData(
                      sectionsSpace: 0,
                      centerSpaceRadius: 35,
                      startDegreeOffset: -90,
                      sections: [
                        PieChartSectionData(
                          color: activeColor,
                          value: percentage,
                          radius: 8,
                          showTitle: false,
                        ),
                        PieChartSectionData(
                          color: ColorResources.whiteColor.withOpacity(0.05),
                          value: 100 - percentage,
                          radius: 6,
                          showTitle: false,
                        ),
                      ],
                    ),
                  ),
                  Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '${percentage.toInt()}%',
                          style: const TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.whiteColor,
                            fontSize: 18,
                            fontWeight: FontWeight.w400,
                          ),
                        ),
                        Text(
                          label,
                          style: TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.liteTextColor,
                            fontSize: 7,
                            letterSpacing: 0.5,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── LEAD CONCENTRATION SECTION ──────────────────────────────
class _LeadConcentrationSection extends StatelessWidget {
  const _LeadConcentrationSection();

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
          Text('LEAD CONCENTRATION', style: AppTextStyles.headingSmall),
          const SizedBox(height: 24),
          Row(
            children: [
              SizedBox(
                height: 140,
                width: 140,
                child: PieChart(
                  PieChartData(
                    sectionsSpace: 4,
                    centerSpaceRadius: 0,
                    sections: [
                      PieChartSectionData(
                        color: ColorResources.primaryColor,
                        value: 40,
                        title: '40%',
                        radius: 70,
                        titleStyle: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      PieChartSectionData(
                        color: ColorResources.primaryColor.withOpacity(0.6),
                        value: 25,
                        title: '25%',
                        radius: 65,
                        titleStyle: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      PieChartSectionData(
                        color: ColorResources.primaryColor.withOpacity(0.3),
                        value: 20,
                        title: '20%',
                        radius: 60,
                        titleStyle: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      PieChartSectionData(
                        color: ColorResources.borderColor,
                        value: 15,
                        title: '15%',
                        radius: 55,
                        titleStyle: const TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                          color: Colors.white60,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 30),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _LeadLegendItem(
                      label: 'INSTAGRAM',
                      percentage: '40%',
                      color: ColorResources.primaryColor,
                    ),
                    const SizedBox(height: 10),
                    _LeadLegendItem(
                      label: 'GOOGLE ADS',
                      percentage: '25%',
                      color: ColorResources.primaryColor.withOpacity(0.6),
                    ),
                    const SizedBox(height: 10),
                    _LeadLegendItem(
                      label: 'WEBSITE',
                      percentage: '20%',
                      color: ColorResources.primaryColor.withOpacity(0.3),
                    ),
                    const SizedBox(height: 10),
                    _LeadLegendItem(
                      label: 'REFERRALS',
                      percentage: '15%',
                      color: ColorResources.borderColor,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _LeadLegendItem extends StatelessWidget {
  final String label;
  final String percentage;
  final Color color;

  const _LeadLegendItem({
    required this.label,
    required this.percentage,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            label,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor.withOpacity(0.6),
              fontSize: 10,
              letterSpacing: 1.0,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Text(
          percentage,
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 11,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}
