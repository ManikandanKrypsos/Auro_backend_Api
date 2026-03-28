import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/custom_appbar.dart';

class TherapistAppointmentDetailScreen extends StatefulWidget {
  const TherapistAppointmentDetailScreen({super.key});

  @override
  State<TherapistAppointmentDetailScreen> createState() =>
      _TherapistAppointmentDetailScreenState();
}

class _TherapistAppointmentDetailScreenState
    extends State<TherapistAppointmentDetailScreen> {
  // ── Status ────────────────────────────────────────────
  String _status = 'UPCOMING'; 

  // ── Static Data ───────────────────────────────────────
  static const _patient = 'Isabelle Morel';
  static const _age = '34';
  static const _gender = 'Female';
  static const _phone = '+91 98765 43210';
  static const _email = 'isabelle.morel@email.com';
  static const _therapistName = 'Sarah Jenkins';

  static const _service = 'Hydra-Facial Platinum';
  static const _session = 2;
  static const _totalSessions = 5;
  static const _duration = '45 mins';
  static const _date = 'Friday, Oct 24, 2024';
  static const _timeRange = '11:45 AM – 12:30 PM';
  static const _room = 'Facial Room 2';

  static const _skinType = 'Combination / Sensitive';
  static const _contraindications =
      'Allergic to Salicylic Acid. Avoid active retinol.';

  static const _nextTreatment =
      'Hydra-Facial Platinum — Session 3 of 5 · Nov 15, 2024';


  static const List<Map<String, dynamic>> _clinicProducts = [
    {'name': 'Gentle Cleanser', 'unit': 'ml'},
    {'name': 'Hyaluronic Acid Serum', 'unit': 'ml'},
    {'name': 'SPF 50 Broad Spectrum', 'unit': 'ml'},
    {'name': 'Calming Rose Toner', 'unit': 'ml'},
    {'name': 'Vitamin C Infusion', 'unit': 'ml'},
    {'name': '24K Gold Facial Serum', 'unit': 'pcs'},
    {'name': 'Retinol Night Cream', 'unit': 'g'},
    {'name': 'Niacinamide Essence', 'unit': 'ml'},
    {'name': 'Collagen Boost Mask', 'unit': 'pcs'},
    {'name': 'Peptide Eye Cream', 'unit': 'g'},
  ];

  final List<Map<String, String>> _notes = [];


  final List<Map<String, dynamic>> _productsUsed = [];

  String? _beforePhoto;
  String? _afterPhoto;



  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: 'SESSION DETAILS'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 180),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeroSection(),
            const SizedBox(height: 14),
               Row(
            children: [
              // Start Session
              Expanded(
                child: _buildActionBtn(
                  label: 'START SESSION',
                  icon: Icons.play_arrow_rounded,
                  enabled: _status == 'UPCOMING',
                  isPrimary: true,
                  onTap: () => _confirmStatusChange(
                    title: 'Start Session?',
                    message:
                        'Are you sure you want to start the session for $_patient?',
                    onConfirm: () => setState(() => _status = 'IN SESSION'),
                  ),
                ),
              ),
              const SizedBox(width: 10),

              // Complete Session
              Expanded(
                child: _buildActionBtn(
                  label: 'COMPLETE SESSION',
                  icon: Icons.check_rounded,
                  enabled: _status == 'IN SESSION',
                  isPrimary: false,
                  onTap: () => _confirmStatusChange(
                    title: 'Complete Session?',
                    message: 'Mark this session as completed for $_patient?',
                    onConfirm: () => setState(() => _status = 'COMPLETED'),
                  ),
                ),
              ),
            ],
          ),
          
           const SizedBox(height: 14),
            _buildPatientSection(),
            const SizedBox(height: 14),
            _buildSection(
              label: 'SERVICE DETAILS',
              child: _buildServiceDetails(),
            ),
            const SizedBox(height: 14),
            _buildSection(label: 'SKIN PROFILE', child: _buildSkinProfile()),
            const SizedBox(height: 14),
            _buildSection(
              label: 'SESSION NOTES',
              actionLabel: '+ ADD NOTE',
              onAction: () => _showAddNoteDialog(),
              child: _buildNotesList(),
            ),
            const SizedBox(height: 14),
            _buildSection(
              label: 'BEFORE PHOTO',
              actionLabel: _beforePhoto == null ? '+ ADD' : 'REPLACE',
              onAction: () {},
              child: _buildPhotoBox(_beforePhoto),
            ),
            const SizedBox(height: 14),
            _buildSection(
              label: 'AFTER PHOTO',
              actionLabel: _afterPhoto == null ? '+ ADD' : 'REPLACE',
              onAction: () {},
              child: _buildPhotoBox(_afterPhoto),
            ),
            const SizedBox(height: 14),
            _buildSection(
              label: 'PRODUCTS USED',
              actionLabel: '+ ADD PRODUCT',
              onAction: () => _showProductPicker(),
              child: _buildProductsList(),
            ),
            const SizedBox(height: 14),
            _buildSection(label: 'NEXT SESSION', child: _buildNextSteps()),
          ],
        ),
      ),

    );
  }

  // ── Hero ──────────────────────────────────────────────
  Widget _buildHeroSection() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 20),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        children: [
          // Avatar
          Container(
            padding: const EdgeInsets.all(3),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: ColorResources.primaryColor, width: 2),
            ),
            child: const CircleAvatar(
              radius: 52,
              backgroundColor: Color(0xFF1A1A1A),
              child: Icon(
                Icons.person,
                color: ColorResources.liteTextColor,
                size: 48,
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Patient name
          const Text(
            _patient,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 28,
              fontWeight: FontWeight.w300,
              fontStyle: FontStyle.italic,
              letterSpacing: 1.0,
            ),
          ),
          const SizedBox(height: 5),

          // Age · Gender
          Text(
            '$_age yrs  ·  $_gender',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.55),
              fontSize: 12,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 10),

          // Therapist
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.person_outline,
                size: 13,
                color: ColorResources.primaryColor.withOpacity(0.7),
              ),
              const SizedBox(width: 5),
              Text(
                _therapistName,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor.withOpacity(0.7),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildStatusBadge(_status),
        ],
      ),
    );
  }

  // ── Patient ───────────────────────────────────────────
  Widget _buildPatientSection() {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(18, 18, 18, 12),
            child: Text(
              'PATIENT DETAILS',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.primaryColor,
                fontSize: 10,
                fontWeight: FontWeight.w600,
                letterSpacing: 2.5,
              ),
            ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(18, 0, 18, 0),
            child: Text(
              _phone,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 22,
                fontWeight: FontWeight.w400,
                letterSpacing: 1.5,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
            child: GestureDetector(
              onTap: () {},
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 15),
                decoration: BoxDecoration(
                  color: ColorResources.primaryColor,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.call_rounded, color: Colors.black, size: 18),
                    SizedBox(width: 10),
                    Text(
                      'Call Patient',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: Colors.black,
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),
          Padding(
            padding: const EdgeInsets.all(18),
            child: _infoRow(Icons.email_outlined, 'Email', _email),
          ),
        ],
      ),
    );
  }

  // ── Service Details ───────────────────────────────────
  Widget _buildServiceDetails() {
    final rows = [
      {'icon': Icons.spa_outlined, 'label': 'Service', 'value': _service},
      {
        'icon': Icons.repeat_rounded,
        'label': 'Session',
        'value': 'Session $_session of $_totalSessions',
      },
      {'icon': Icons.timer_outlined, 'label': 'Duration', 'value': _duration},
      {'icon': Icons.calendar_today_outlined, 'label': 'Date', 'value': _date},
      {'icon': Icons.access_time_rounded, 'label': 'Time', 'value': _timeRange},
      {'icon': Icons.meeting_room_outlined, 'label': 'Room', 'value': _room},
    ];

    return Column(
      children: rows.asMap().entries.map((e) {
        final r = e.value;
        return Column(
          children: [
            if (e.key > 0)
              Divider(
                color: ColorResources.borderColor,
                height: 1,
                thickness: 0.5,
              ),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 13),
              child: Row(
                children: [
                  Icon(
                    r['icon'] as IconData,
                    size: 16,
                    color: ColorResources.primaryColor.withOpacity(0.7),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    r['label'] as String,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.7),
                      fontSize: 14,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    r['value'] as String,
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      }).toList(),
    );
  }

  // ── Skin Profile ──────────────────────────────────────
  Widget _buildSkinProfile() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _infoRow(Icons.face_retouching_natural, 'Skin Type', _skinType),
        const SizedBox(height: 14),
        Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),
        const SizedBox(height: 14),
        Text(
          'CONTRAINDICATIONS',
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.negativeColor.withOpacity(0.8),
            fontSize: 9,
            fontWeight: FontWeight.w700,
            letterSpacing: 2,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: ColorResources.negativeColor.withOpacity(0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: ColorResources.negativeColor.withOpacity(0.2),
              width: 0.5,
            ),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                Icons.warning_amber_rounded,
                size: 14,
                color: ColorResources.negativeColor.withOpacity(0.6),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  _contraindications,
                  style: AppTextStyles.bodyItalic.copyWith(fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ── Notes ─────────────────────────────────────────────
  Widget _buildNotesList() {
    if (_notes.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 20),
        decoration: BoxDecoration(
          color: ColorResources.blackColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Column(
          children: [
            Icon(
              Icons.edit_note_outlined,
              size: 24,
              color: ColorResources.liteTextColor,
            ),
            const SizedBox(height: 6),
            Text(
              'NO NOTES YET. TAP + ADD NOTE.',
          style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 10,
                fontWeight: FontWeight.w600,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      children: _notes.asMap().entries.map((e) {
        final i = e.key;
        final note = e.value;
        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: ColorResources.blackColor,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: ColorResources.borderColor, width: 0.5),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      note['title']!,
                      style: const TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.3,
                      ),
                    ),
                  ),
                  // Edit
                  GestureDetector(
                    onTap: () => _showAddNoteDialog(index: i),
                    child: Icon(
                      Icons.edit_outlined,
                      size: 15,
                      color: ColorResources.primaryColor.withOpacity(0.7),
                    ),
                  ),
                  const SizedBox(width: 12),
                  // Delete
                  GestureDetector(
                    onTap: () => _confirmDeleteNote(i),
                    child: Icon(
                      Icons.delete_outline,
                      size: 15,
                      color: ColorResources.negativeColor.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                note['description']!,
                style: AppTextStyles.bodyItalic.copyWith(fontSize: 13),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  // ── Photos ────────────────────────────────────────────
  Widget _buildPhotoBox(String? photoPath) {
    if (photoPath != null) {
      return Container(
        height: 120,
        width: double.infinity,
        decoration: BoxDecoration(
          color: ColorResources.blackColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: const Center(
          child: Icon(Icons.image, color: ColorResources.liteTextColor, size: 30),
        ),
      );
    }

    return GestureDetector(
      onTap: () {},
      child: Container(
        height: 100,
        width: double.infinity,
        decoration: BoxDecoration(
          color: ColorResources.blackColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: ColorResources.borderColor,
            width: 0.5,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.add_a_photo_outlined,
              size: 24,
              color: ColorResources.liteTextColor,
            ),
            const SizedBox(height: 8),
            Text(
              'TAP TO UPLOAD PHOTO',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 10,
                fontWeight: FontWeight.w600,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Products ──────────────────────────────────────────
  Widget _buildProductsList() {
    if (_productsUsed.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 20),
        decoration: BoxDecoration(
          color: ColorResources.blackColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Column(
          children: [
            Icon(
              Icons.science_outlined,
              size: 24,
              color: ColorResources.liteTextColor,
            ),
            const SizedBox(height: 6),
            Text(
              'NO PRODUCT USED YET.',
                  style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 10,
                fontWeight: FontWeight.w600,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      children: _productsUsed.asMap().entries.map((e) {
        final p = e.value;
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: ColorResources.blackColor,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: ColorResources.borderColor, width: 0.5),
          ),
          child: Row(
            children: [
              Container(
                width: 6,
                height: 6,
                decoration: const BoxDecoration(
                  color: ColorResources.primaryColor,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  p['name'] as String,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),
              Text(
                '${p['quantity']} ${p['unit']}',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor.withOpacity(0.7),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 12),
              GestureDetector(
                onTap: () => setState(() => _productsUsed.removeAt(e.key)),
                child: Icon(
                  Icons.close_rounded,
                  size: 14,
                  color: ColorResources.liteTextColor.withOpacity(0.4),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  // ── Next Steps ────────────────────────────────────────
  Widget _buildNextSteps() {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: ColorResources.primaryColor.withOpacity(0.08),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: ColorResources.primaryColor.withOpacity(0.2),
              width: 0.5,
            ),
          ),
          child: const Icon(
            Icons.event_outlined,
            size: 18,
            color: ColorResources.primaryColor,
          ),
        ),
        const SizedBox(width: 14),
        const Expanded(
          child: Text(
            _nextTreatment,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 14,
              letterSpacing: 0.3,
              height: 1.4,
            ),
          ),
        ),
      ],
    );
  }



  Widget _buildActionBtn({
    required String label,
    required IconData icon,
    required bool enabled,
    required bool isPrimary,
    required VoidCallback onTap,
  }) {
    final Color bg = isPrimary
        ? (enabled
              ? ColorResources.primaryColor
              : ColorResources.primaryColor.withOpacity(0.25))
        : (enabled
              ? ColorResources.cardColor
              : ColorResources.cardColor.withOpacity(0.5));

    final Color fg = isPrimary
        ? (enabled ? Colors.black : Colors.black.withOpacity(0.3))
        : (enabled
              ? ColorResources.primaryColor
              : ColorResources.primaryColor.withOpacity(0.3));

    final Color borderColor = isPrimary
        ? Colors.transparent
        : (enabled
              ? ColorResources.primaryColor.withOpacity(0.5)
              : ColorResources.borderColor);

    return GestureDetector(
      onTap: enabled ? onTap : null,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: borderColor, width: 0.8),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 16, color: fg),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: fg,
                fontSize: 12,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Confirm Dialog ────────────────────────────────────
  void _confirmStatusChange({
    required String title,
    required String message,
    required VoidCallback onConfirm,
  }) {
    Get.dialog(
      Dialog(
        backgroundColor: ColorResources.cardColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                message,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.liteTextColor.withOpacity(0.7),
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: () => Get.back(),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: ColorResources.blackColor,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: ColorResources.borderColor,
                            width: 0.5,
                          ),
                        ),
                        child: const Center(
                          child: Text(
                            'CANCEL',
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.liteTextColor,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: GestureDetector(
                      onTap: () {
                        Get.back();
                        onConfirm();
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: ColorResources.primaryColor,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Center(
                          child: Text(
                            'CONFIRM',
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: Colors.black,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Add / Edit Note Dialog ────────────────────────────
  void _showAddNoteDialog({int? index}) {
    final titleCtrl = TextEditingController(
      text: index != null ? _notes[index]['title'] : '',
    );
    final descCtrl = TextEditingController(
      text: index != null ? _notes[index]['description'] : '',
    );

    Get.dialog(
      Dialog(
        backgroundColor: ColorResources.cardColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                index != null ? 'EDIT NOTE' : 'ADD NOTE',
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 2.5,
                ),
              ),
              const SizedBox(height: 16),

              // Title
              _dialogTextField(titleCtrl, 'Note title...'),
              const SizedBox(height: 12),

              // Description
              _dialogTextField(
                descCtrl,
                'Write your note here...',
                maxLines: 4,
              ),
              const SizedBox(height: 20),

              Row(
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: () => Get.back(),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: ColorResources.blackColor,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: ColorResources.borderColor,
                            width: 0.5,
                          ),
                        ),
                        child: const Center(
                          child: Text(
                            'CANCEL',
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.liteTextColor,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: GestureDetector(
                      onTap: () {
                        if (titleCtrl.text.trim().isEmpty) return;
                        setState(() {
                          final note = {
                            'title': titleCtrl.text.trim(),
                            'description': descCtrl.text.trim(),
                          };
                          if (index != null) {
                            _notes[index] = note;
                          } else {
                            _notes.add(note);
                          }
                        });
                        Get.back();
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: ColorResources.primaryColor,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Center(
                          child: Text(
                            index != null ? 'UPDATE' : 'SAVE',
                            style: const TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: Colors.black,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Delete Note Confirm ───────────────────────────────
  void _confirmDeleteNote(int index) {
    Get.dialog(
      Dialog(
        backgroundColor: ColorResources.cardColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'DELETE NOTE',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Are you sure you want to delete this note?',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.liteTextColor.withOpacity(0.7),
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: () => Get.back(),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: ColorResources.blackColor,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: ColorResources.borderColor,
                            width: 0.5,
                          ),
                        ),
                        child: const Center(
                          child: Text(
                            'CANCEL',
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.liteTextColor,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: GestureDetector(
                      onTap: () {
                        setState(() => _notes.removeAt(index));
                        Get.back();
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: ColorResources.negativeColor.withOpacity(0.8),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Center(
                          child: Text(
                            'DELETE',
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Product Picker ────────────────────────────────────
  void _showProductPicker() {
    final searchCtrl = TextEditingController();
    List<Map<String, dynamic>> filtered = List.from(_clinicProducts);
    final qtyCtrl = TextEditingController(text: '1');
    Map<String, dynamic>? selectedProduct;

    Get.dialog(
      StatefulBuilder(
        builder: (ctx, setDlg) => Dialog(
          backgroundColor: ColorResources.cardColor,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'SELECT PRODUCT',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 2.5,
                  ),
                ),
                const SizedBox(height: 14),

                // Search
                _dialogTextField(
                  searchCtrl,
                  'Search product...',
                  onChanged: (v) {
                    setDlg(() {
                      filtered = _clinicProducts
                          .where(
                            (p) => (p['name'] as String).toLowerCase().contains(
                              v.toLowerCase(),
                            ),
                          )
                          .toList();
                    });
                  },
                ),
                const SizedBox(height: 10),

                // Product list
                SizedBox(
                  height: 180,
                  child: ListView.builder(
                    itemCount: filtered.length,
                    itemBuilder: (_, i) {
                      final p = filtered[i];
                      final isSel = selectedProduct == p;
                      return GestureDetector(
                        onTap: () => setDlg(() => selectedProduct = p),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 6),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 10,
                          ),
                          decoration: BoxDecoration(
                            color: isSel
                                ? ColorResources.primaryColor.withOpacity(0.1)
                                : ColorResources.blackColor,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: isSel
                                  ? ColorResources.primaryColor
                                  : ColorResources.borderColor,
                              width: isSel ? 0.8 : 0.5,
                            ),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  p['name'] as String,
                                  style: TextStyle(
                                    fontFamily: 'CormorantGaramond',
                                    color: isSel
                                        ? ColorResources.primaryColor
                                        : ColorResources.whiteColor,
                                    fontSize: 14,
                                    fontWeight: isSel
                                        ? FontWeight.w600
                                        : FontWeight.w400,
                                  ),
                                ),
                              ),
                              if (isSel)
                                Icon(
                                  Icons.check,
                                  size: 14,
                                  color: ColorResources.primaryColor,
                                ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),

                // Quantity
                if (selectedProduct != null) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Text(
                        'QUANTITY (${selectedProduct!['unit']})',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor.withOpacity(0.5),
                          fontSize: 9,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 2,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _dialogTextField(
                          qtyCtrl,
                          '1',
                          keyboardType: TextInputType.number,
                        ),
                      ),
                    ],
                  ),
                ],

                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: () => Get.back(),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 13),
                          decoration: BoxDecoration(
                            color: ColorResources.blackColor,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: ColorResources.borderColor,
                              width: 0.5,
                            ),
                          ),
                          child: const Center(
                            child: Text(
                              'CANCEL',
                              style: TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: ColorResources.liteTextColor,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 1.5,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: GestureDetector(
                        onTap: () {
                          if (selectedProduct == null) return;
                          setState(() {
                            _productsUsed.add({
                              'name': selectedProduct!['name'],
                              'unit': selectedProduct!['unit'],
                              'quantity': int.tryParse(qtyCtrl.text) ?? 1,
                            });
                          });
                          Get.back();
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 13),
                          decoration: BoxDecoration(
                            color: ColorResources.primaryColor,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Center(
                            child: Text(
                              'ADD',
                              style: TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: Colors.black,
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.5,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ── Dialog TextField ──────────────────────────────────
  Widget _dialogTextField(
    TextEditingController ctrl,
    String hint, {
    int maxLines = 1,
    TextInputType keyboardType = TextInputType.text,
    ValueChanged<String>? onChanged,
  }) {
    return TextField(
      controller: ctrl,
      maxLines: maxLines,
      keyboardType: keyboardType,
      onChanged: onChanged,
      style: const TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.whiteColor,
        fontSize: 14,
      ),
      cursorColor: ColorResources.primaryColor,
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.whiteColor.withOpacity(0.25),
          fontSize: 14,
          fontStyle: FontStyle.italic,
        ),
        filled: true,
        fillColor: ColorResources.blackColor,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 12,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
            color: ColorResources.borderColor,
            width: 0.5,
          ),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
            color: ColorResources.borderColor,
            width: 0.5,
          ),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(
            color: ColorResources.primaryColor,
            width: 0.8,
          ),
        ),
      ),
    );
  }

  // ── Section Card ──────────────────────────────────────
  Widget _buildSection({
    required String label,
    required Widget child,
    String? actionLabel,
    VoidCallback? onAction,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 2.5,
                ),
              ),
              if (actionLabel != null)
                GestureDetector(
                  onTap: onAction,
                  child: Text(
                    actionLabel,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.5,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }

  // ── Info Row ──────────────────────────────────────────
  Widget _infoRow(IconData icon, String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label.toUpperCase(),
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor.withOpacity(0.5),
            fontSize: 9,
            fontWeight: FontWeight.w600,
            letterSpacing: 2,
          ),
        ),
        const SizedBox(height: 5),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              icon,
              size: 13,
              color: ColorResources.liteTextColor.withOpacity(0.5),
            ),
            const SizedBox(width: 7),
            Expanded(
              child: Text(
                value,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 14,
                  fontWeight: FontWeight.w400,
                  letterSpacing: 0.2,
                  height: 1.3,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ── Status Badge ──────────────────────────────────────
  Widget _buildStatusBadge(String status) {
    Color color;
    switch (status) {
      case 'COMPLETED':
        color = const Color(0xFF5C7A5C);
        break;
      case 'IN SESSION':
        color = ColorResources.primaryColor;
        break;
      default:
        color = const Color(0xFF6A6A6A);
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withOpacity(0.4), width: 0.8),
      ),
      child: Text(
        status,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w700,
          letterSpacing: 2,
        ),
      ),
    );
  }
}
