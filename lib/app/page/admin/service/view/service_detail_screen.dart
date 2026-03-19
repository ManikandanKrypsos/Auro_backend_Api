import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:flutter/material.dart';
import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';

class ServiceDetailScreen extends StatelessWidget {
  const ServiceDetailScreen({super.key});

  // ── Static demo data ──────────────────────────────────
  static const _name = 'Signature Gold Facial';
  static const _category = 'FACE';
  static const _status = 'ACTIVE';
  static const _price = '\$250';
  static const _duration = '60 min';
  static const _description =
      'Revitalizing 24k gold leaf therapy for instant luminosity and deep cellular renewal. This premium treatment combines ancient gold healing properties with modern skincare science.';
  static const _image =
      'https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=800';

  // Protocol
  static const _preCare =
      'Avoid sun exposure for 24 hours prior. Remove all makeup before arrival. Do not use retinol or AHA/BHA products 48 hours before.';
  static const _postCare =
      'Apply SPF 50+ daily. Avoid heavy exercise for 24 hours. Use recommended hydrating serum twice daily.';
  static const _contraindications = [
    'Pregnancy',
    'Active Infection',
    'Blood Thinners',
    'Sunburn',
  ];

  // Session
  static const _frequency = 'Every 2 Weeks';
  static const _packageSessions = '6 Sessions';

  // Resources
  static const _room = 'Therapy Suite A';
  static const _equipment = ['LED Light Panel', 'Ultrasound Probe'];
  static const _consumables = ['SERUM', 'MASK', 'SPF CREAM'];

  // Staff
  static const _staff = [
    {'name': 'Elena Sterling', 'role': 'Senior Wellness Therapist'},
    {'name': 'Maya Ross', 'role': 'Dermal Clinician'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: CustomAppBar(title: 'SERVICE DETAIL'),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Hero image ──────────────────────────────
            _HeroImage(imageUrl: _image, status: _status, category: _category),

            const SizedBox(height: 20),

            // ── Name + Price + Duration ──────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          _name,
                          style: const TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.whiteColor,
                            fontSize: 28,
                            fontWeight: FontWeight.w300,
                            letterSpacing: 0.5,
                            height: 1.2,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        _price,
                        style: const TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.primaryColor,
                          fontSize: 28,
                          fontWeight: FontWeight.w300,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(
                        Icons.timer_outlined,
                        color: ColorResources.primaryColor,
                        size: 13,
                      ),
                      const SizedBox(width: 5),
                      Text(
                        _duration,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor,
                          fontSize: 13,
                          letterSpacing: 1.0,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  Text(
                    _description,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor.withOpacity(0.6),
                      fontSize: 14,
                      height: 1.6,
                      letterSpacing: 0.2,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── Quick stats row ──────────────────────────
            const _QuickStats(),

            const SizedBox(height: 28),

            // ── Treatment Protocol ───────────────────────
            _sectionHeader(
              Icons.medical_services_outlined,
              'TREATMENT PROTOCOL',
            ),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                children: [
                  _InfoCard(
                    icon: Icons.wb_sunny_outlined,
                    label: 'PRE-CARE',
                    value: _preCare,
                  ),
                  const SizedBox(height: 10),
                  _InfoCard(
                    icon: Icons.healing_outlined,
                    label: 'POST-CARE',
                    value: _postCare,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _subLabel('CONTRAINDICATIONS'),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _contraindications
                        .map((c) => _Chip(label: c))
                        .toList(),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── Session Recommendation ───────────────────
            _sectionHeader(
              Icons.event_repeat_outlined,
              'SESSION RECOMMENDATION',
            ),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Container(
                decoration: BoxDecoration(
                  color: ColorResources.cardColor,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: ColorResources.borderColor,
                    width: 0.5,
                  ),
                ),
                child: Column(
                  children: [
                    _DetailRow(
                      icon: Icons.repeat_outlined,
                      label: 'FREQUENCY',
                      value: _frequency,
                    ),
                    Divider(
                      color: ColorResources.borderColor,
                      height: 1,
                      thickness: 0.5,
                    ),
                    _DetailRow(
                      icon: Icons.layers_outlined,
                      label: 'PACKAGE',
                      value: _packageSessions,
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 28),

            // ── Resources ───────────────────────────────
            _sectionHeader(Icons.inventory_2_outlined, 'RESOURCES'),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    decoration: BoxDecoration(
                      color: ColorResources.cardColor,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: ColorResources.borderColor,
                        width: 0.5,
                      ),
                    ),
                    child: _DetailRow(
                      icon: Icons.meeting_room_outlined,
                      label: 'ROOM',
                      value: _room,
                    ),
                  ),
                  const SizedBox(height: 16),
                  _subLabel('EQUIPMENT'),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _equipment.map((e) => _Chip(label: e)).toList(),
                  ),
                  const SizedBox(height: 16),
                  _subLabel('CONSUMABLES'),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _consumables.map((c) => _Chip(label: c)).toList(),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── Staff Assignment ─────────────────────────
            _sectionHeader(Icons.people_outline, 'STAFF ASSIGNMENT'),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                children: _staff
                    .map((s) => _StaffCard(name: s['name']!, role: s['role']!))
                    .toList(),
              ),
            ),

            const SizedBox(height: 28),

            // ── Edit button ──────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: GestureDetector(
                onTap: () {},
                child: Container(
                  width: double.infinity,
                  height: 52,
                  decoration: BoxDecoration(
                    color: ColorResources.primaryColor,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(Icons.edit_outlined, color: Colors.black, size: 16),
                      SizedBox(width: 10),
                      Text(
                        'EDIT SERVICE',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: Colors.black,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 3.0,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // ── Delete ───────────────────────────────────
            Center(
              child: TextButton(
                onPressed: () {},
                child: Text(
                  'DELETE SERVICE',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.negativeColor.withOpacity(0.7),
                    fontSize: 11,
                    letterSpacing: 2.0,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  // ── Section header ──────────────────────────────────────
  Widget _sectionHeader(IconData icon, String label) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          Icon(icon, color: ColorResources.primaryColor, size: 16),
          const SizedBox(width: 10),
          Text(
            label,
            style: AppTextStyles.headingSmall.copyWith(
              fontSize: 11,
              color: ColorResources.liteTextColor,
              letterSpacing: 3.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _subLabel(String label) {
    return Text(
      label,
      style: AppTextStyles.headingSmall.copyWith(
        fontSize: 9,
        color: ColorResources.liteTextColor,
        letterSpacing: 2.5,
      ),
    );
  }
}

// ── HERO IMAGE ─────────────────────────────────────────────
class _HeroImage extends StatelessWidget {
  final String imageUrl;
  final String status;
  final String category;

  const _HeroImage({
    required this.imageUrl,
    required this.status,
    required this.category,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Image
        SizedBox(
          height: 260,
          width: double.infinity,
          child: Image.network(
            imageUrl,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(
              height: 260,
              color: ColorResources.cardColor,
              child: Icon(
                Icons.image_outlined,
                color: ColorResources.primaryColor.withOpacity(0.3),
                size: 40,
              ),
            ),
          ),
        ),
        // Gradient overlay
        Positioned.fill(
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.transparent,
                  ColorResources.blackColor.withOpacity(0.85),
                ],
                stops: const [0.45, 1.0],
              ),
            ),
          ),
        ),
        // Status badge — top right
        Positioned(
          top: 16,
          right: 16,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.6),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(
                color: ColorResources.primaryColor.withOpacity(0.5),
                width: 0.5,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 5,
                  height: 5,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: ColorResources.primaryColor,
                  ),
                ),
                const SizedBox(width: 5),
                Text(
                  status,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ),
        // Category badge — bottom left
        Positioned(
          bottom: 16,
          left: 20,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: ColorResources.primaryColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(
                color: ColorResources.primaryColor.withOpacity(0.4),
                width: 0.5,
              ),
            ),
            child: Text(
              category,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.primaryColor,
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 2.5,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ── QUICK STATS ────────────────────────────────────────────
class _QuickStats extends StatelessWidget {
  const _QuickStats();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Row(
          children: [
            _statCell(Icons.event_outlined, '48', 'SESSIONS'),
            _vDivider(),
            _statCell(Icons.star_outline, '4.9', 'RATING'),
            _vDivider(),
            _statCell(Icons.people_outline, '2', 'THERAPISTS'),
          ],
        ),
      ),
    );
  }

  Widget _statCell(IconData icon, String value, String label) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Column(
          children: [
            Icon(icon, color: ColorResources.primaryColor, size: 16),
            const SizedBox(height: 6),
            Text(
              value,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor,
                fontSize: 9,
                letterSpacing: 1.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _vDivider() =>
      Container(width: 0.5, height: 52, color: ColorResources.borderColor);
}

// ── INFO CARD (pre/post care) ──────────────────────────────
class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoCard({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: ColorResources.primaryColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: ColorResources.primaryColor.withOpacity(0.25),
                width: 0.5,
              ),
            ),
            child: Icon(icon, color: ColorResources.primaryColor, size: 15),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor,
                    fontSize: 9,
                    letterSpacing: 2.0,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  value,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor.withOpacity(0.75),
                    fontSize: 14,
                    height: 1.5,
                    letterSpacing: 0.2,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── DETAIL ROW ─────────────────────────────────────────────
class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Icon(icon, color: ColorResources.primaryColor, size: 14),
          const SizedBox(width: 12),
          Text(
            label,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor,
              fontSize: 10,
              letterSpacing: 2.0,
              fontWeight: FontWeight.w600,
            ),
          ),
          const Spacer(),
          Text(
            value,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 14,
              fontWeight: FontWeight.w400,
              letterSpacing: 0.3,
            ),
          ),
        ],
      ),
    );
  }
}

// ── CHIP ───────────────────────────────────────────────────
class _Chip extends StatelessWidget {
  final String label;
  const _Chip({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: ColorResources.primaryColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: ColorResources.primaryColor.withOpacity(0.3),
          width: 0.5,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.primaryColor,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.5,
        ),
      ),
    );
  }
}

// ── STAFF CARD ─────────────────────────────────────────────
class _StaffCard extends StatelessWidget {
  final String name;
  final String role;
  const _StaffCard({required this.name, required this.role});

  @override
  Widget build(BuildContext context) {
    final initials = name
        .split(' ')
        .take(2)
        .map((w) => w[0].toUpperCase())
        .join();

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: ColorResources.primaryColor.withOpacity(0.12),
              shape: BoxShape.circle,
              border: Border.all(
                color: ColorResources.primaryColor.withOpacity(0.4),
                width: 0.8,
              ),
            ),
            alignment: Alignment.center,
            child: Text(
              initials,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.primaryColor,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                name,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 15,
                  fontWeight: FontWeight.w400,
                  letterSpacing: 0.3,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                role,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.liteTextColor,
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                  letterSpacing: 0.2,
                ),
              ),
            ],
          ),
          const Spacer(),
          Icon(
            Icons.chevron_right,
            color: ColorResources.liteTextColor,
            size: 18,
          ),
        ],
      ),
    );
  }
}
