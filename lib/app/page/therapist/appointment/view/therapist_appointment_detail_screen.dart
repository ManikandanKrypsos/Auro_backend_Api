import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../theme/color/color.dart';
import '../../../../widgets/custom_appbar.dart';

class TherapistAppointmentDetailScreen extends StatefulWidget {
  const TherapistAppointmentDetailScreen({super.key});

  @override
  State<TherapistAppointmentDetailScreen> createState() =>
      _TherapistAppointmentDetailScreenState();
}

class _TherapistAppointmentDetailScreenState
    extends State<TherapistAppointmentDetailScreen> {
  // ── Session status ────────────────────────────────────
  String _status = 'UPCOMING'; // UPCOMING → IN SESSION → COMPLETED

  // ── Static patient data ───────────────────────────────
  static const _patientName = 'Isabelle Morel';
  static const _patientAge = '34';
  static const _patientGender = 'Female';
  static const _patientPhone = '+91 98765 43210';
  static const _patientEmail = 'isabelle.morel@email.com';
  static const _therapistName = 'Sarah Jenkins';

  // ── Static service data ───────────────────────────────
  static const _service = 'Hydra-Facial Platinum';
  static const _session = 2;
  static const _totalSessions = 5;
  static const _duration = '45 mins';
  static const _date = 'Friday, Oct 24, 2024';
  static const _timeRange = '11:45 AM – 12:30 PM';
  static const _room = 'Facial Room 2';
  static const _packageName = 'Hydra-Facial Platinum Pack';

  // ── Static skin profile ───────────────────────────────
  static const _skinType = 'Combination / Sensitive';
  static const _fitzpatrick = 'Type III';
  static const _contraindications =
      'Allergic to Salicylic Acid. Avoid active retinol. No chemical exfoliants.';
  static const _allergies = 'Salicylic Acid, Fragrance compounds';

  // ── Next session ──────────────────────────────────────
  static const _nextSessionLabel =
      'Hydra-Facial Platinum · Session 3 of 5 · Nov 15, 2024';

  // ── Clinic product catalog ────────────────────────────
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
    {'name': 'AHA Resurfacing Toner', 'unit': 'ml'},
    {'name': 'Brightening Ampoule', 'unit': 'ml'},
  ];

  // ── Mutable session data ──────────────────────────────
  // Skin observation (therapist writes during session)
  final _skinObsController = TextEditingController();
  bool _skinObsEditing = false;
  String _savedSkinObs = '';

  // Notes (multiple, add/edit/delete)
  final List<Map<String, String>> _notes = [];

  // Products used in session
  final List<Map<String, dynamic>> _productsUsed = [];

  // Products recommended to patient

  // Photos
  String? _beforePhoto;
  String? _afterPhoto;

  // Next session suggestion
  String _nextSessionSuggestion = '';

  @override
  void dispose() {
    _skinObsController.dispose();
    super.dispose();
  }

  // ─────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: 'SESSION DETAILS'),
      body: Stack(
        children: [
          SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 120),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Hero ──────────────────────────
                _buildHero(),
                const SizedBox(height: 14),

                // ── Action buttons ─────────────────
                _buildActionButtons(),
                const SizedBox(height: 14),

                // ── Patient Details ────────────────
                _buildPatientCard(),
                const SizedBox(height: 14),

                // ── Service Details ────────────────
                _buildSectionCard(
                  label: 'SERVICE DETAILS',
                  child: _buildServiceDetails(),
                ),
                const SizedBox(height: 14),

                // ── Skin Profile ───────────────────
                _buildSectionCard(
                  label: 'SKIN PROFILE',
                  child: _buildSkinProfile(),
                ),
                const SizedBox(height: 14),

                // ── Skin Observation Today ─────────
                _buildSectionCard(
                  label: 'SKIN OBSERVATION TODAY',
                  actionLabel: _skinObsEditing
                      ? null
                      : (_savedSkinObs.isEmpty ? '+ WRITE' : 'EDIT'),
                  onAction: _savedSkinObs.isEmpty && !_skinObsEditing
                      ? () => setState(() => _skinObsEditing = true)
                      : !_skinObsEditing
                      ? () {
                          _skinObsController.text = _savedSkinObs;
                          setState(() => _skinObsEditing = true);
                        }
                      : null,
                  child: _buildSkinObservation(),
                ),
                const SizedBox(height: 14),

                // ── Session Notes ──────────────────
                _buildSectionCard(
                  label: 'SESSION NOTES',
                  actionLabel: '+ ADD NOTE',
                  onAction: () => _showNoteDialog(),
                  child: _buildNotesList(),
                ),
                const SizedBox(height: 14),

                // ── Before & After ──────────────────
                _buildSectionCard(
                  label: 'BEFORE & AFTER',
                  child: _buildBeforeAfter(),
                ),
                const SizedBox(height: 14),

                // ── Products Used ──────────────────
                _buildSectionCard(
                  label: 'PRODUCTS USED IN SESSION',
                  actionLabel: '+ ADD',
                  onAction: () => _showProductPicker(isRecommended: false),
                  child: _buildProductList(_productsUsed, false),
                ),
                const SizedBox(height: 14),

                // ── Next Session ───────────────────
                _buildSectionCard(
                  label: 'NEXT SESSION',
                  child: _buildNextSession(),
                ),
                const SizedBox(height: 14),
              ],
            ),
          ),

          // ── Fixed Save Bar ─────────────────────────
          _buildSaveBar(),
        ],
      ),
    );
  }

  // ── HERO ──────────────────────────────────────────────
  Widget _buildHero() {
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

          const Text(
            _patientName,
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

          Text(
            '$_patientAge yrs  ·  $_patientGender',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.6),
              fontSize: 12,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 10),

          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.person_outline,
                size: 12,
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
          _StatusBadge(status: _status),
        ],
      ),
    );
  }

  // ── ACTION BUTTONS ────────────────────────────────────
  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: _ActionBtn(
            label: 'START SESSION',
            icon: Icons.play_arrow_rounded,
            enabled: _status == 'UPCOMING',
            isPrimary: true,
            onTap: () => _confirmAction(
              title: 'Start Session?',
              message: 'Start the session for $_patientName?',
              confirmLabel: 'START',
              onConfirm: () => setState(() => _status = 'IN SESSION'),
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _ActionBtn(
            label: 'COMPLETE',
            icon: Icons.check_rounded,
            enabled: _status == 'IN SESSION',
            isPrimary: false,
            onTap: () => _confirmAction(
              title: 'Complete Session?',
              message: 'Mark this session as completed for $_patientName?',
              confirmLabel: 'COMPLETE',
              onConfirm: () => setState(() => _status = 'COMPLETED'),
            ),
          ),
        ),
      ],
    );
  }

  // ── PATIENT CARD ──────────────────────────────────────
  Widget _buildPatientCard() {
    return Container(
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(18, 18, 18, 10),
            child: Text(
              'PATIENT CONTACT',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.primaryColor,
                fontSize: 10,
                fontWeight: FontWeight.w600,
                letterSpacing: 2.5,
              ),
            ),
          ),

          // Phone number large
          const Padding(
            padding: EdgeInsets.fromLTRB(18, 0, 18, 14),
            child: Text(
              _patientPhone,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 22,
                fontWeight: FontWeight.w400,
                letterSpacing: 1.5,
              ),
            ),
          ),

          // Call button
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 16),
            child: GestureDetector(
              onTap: () {},
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: ColorResources.primaryColor,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.call_rounded, color: Colors.black, size: 16),
                    SizedBox(width: 8),
                    Text(
                      'Call Patient',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: Colors.black,
                        fontSize: 14,
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

          // Email
          Padding(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: [
                Icon(
                  Icons.email_outlined,
                  size: 13,
                  color: ColorResources.liteTextColor.withOpacity(0.5),
                ),
                const SizedBox(width: 8),
                Text(
                  _patientEmail,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.7),
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── SERVICE DETAILS ───────────────────────────────────
  Widget _buildServiceDetails() {
    final rows = [
      {'icon': Icons.spa_outlined, 'label': 'Service', 'value': _service},
      {
        'icon': Icons.inventory_2_outlined,
        'label': 'Package',
        'value': _packageName,
      },
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
      children: rows.asMap().entries.map((entry) {
        final i = entry.key;
        final r = entry.value;
        return Column(
          children: [
            if (i > 0)
              Divider(
                color: ColorResources.borderColor,
                height: 1,
                thickness: 0.5,
              ),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Row(
                children: [
                  Icon(
                    r['icon'] as IconData,
                    size: 15,
                    color: ColorResources.primaryColor.withOpacity(0.65),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    r['label'] as String,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.65),
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

  // ── SKIN PROFILE ──────────────────────────────────────
  Widget _buildSkinProfile() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Skin type + Fitzpatrick
        Row(
          children: [
            Expanded(
              child: _infoCell(
                Icons.face_retouching_natural,
                'SKIN TYPE',
                _skinType,
                ColorResources.whiteColor,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: _infoCell(
                Icons.palette_outlined,
                'FITZPATRICK',
                _fitzpatrick,
                ColorResources.primaryColor,
              ),
            ),
          ],
        ),

        const SizedBox(height: 14),
        Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),
        const SizedBox(height: 14),

        // Allergies
        _labelledBlock(
          'ALLERGIES',
          _allergies,
          ColorResources.negativeColor,
          Icons.science_outlined,
        ),

        const SizedBox(height: 12),

        // Contraindications — highlighted
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
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.negativeColor.withOpacity(0.8),
                    fontSize: 13,
                    fontStyle: FontStyle.italic,
                    height: 1.45,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ── SKIN OBSERVATION TODAY ────────────────────────────
  Widget _buildSkinObservation() {
    if (!_skinObsEditing && _savedSkinObs.isEmpty) {
      return _emptyState(
        Icons.edit_note_outlined,
        'TAP "+ WRITE" TO ADD OBSERVATION',
      );
    }

    if (_skinObsEditing) {
      return Column(
        children: [
          _styledTextField(
            _skinObsController,
            'Describe today\'s skin condition, reactions, texture, tone...',
            maxLines: 4,
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _outlineBtn(
                  label: 'CANCEL',
                  onTap: () => setState(() {
                    _skinObsEditing = false;
                    _skinObsController.clear();
                  }),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _primaryBtn(
                  label: 'SAVE',
                  onTap: () => setState(() {
                    _savedSkinObs = _skinObsController.text.trim();
                    _skinObsEditing = false;
                  }),
                ),
              ),
            ],
          ),
        ],
      );
    }

    // Saved state
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: ColorResources.blackColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Text(
        _savedSkinObs,
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.whiteColor.withOpacity(0.8),
          fontSize: 14,
          height: 1.5,
        ),
      ),
    );
  }

  // ── NOTES LIST ────────────────────────────────────────
  Widget _buildNotesList() {
    if (_notes.isEmpty) {
      return _emptyState(
        Icons.edit_note_outlined,
        'NO NOTES YET. TAP "+ ADD NOTE".',
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
                  GestureDetector(
                    onTap: () => _showNoteDialog(index: i),
                    child: Icon(
                      Icons.edit_outlined,
                      size: 15,
                      color: ColorResources.primaryColor.withOpacity(0.7),
                    ),
                  ),
                  const SizedBox(width: 12),
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
              if (note['description']!.isNotEmpty) ...[
                const SizedBox(height: 7),
                Text(
                  note['description']!,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor.withOpacity(0.6),
                    fontSize: 13,
                    fontStyle: FontStyle.italic,
                    height: 1.45,
                  ),
                ),
              ],
            ],
          ),
        );
      }).toList(),
    );
  }

  // ── BEFORE & AFTER ────────────────────────────────────
  Widget _buildBeforeAfter() {
    return Row(
      children: [
        Expanded(child: _photoBox('BEFORE', _beforePhoto, false)),
        const SizedBox(width: 12),
        Expanded(child: _photoBox('AFTER', _afterPhoto, true)),
      ],
    );
  }

  Widget _photoBox(String label, String? photoPath, bool isAfter) {
    final labelColor = isAfter
        ? ColorResources.positiveColor
        : ColorResources.liteTextColor;
    final borderColor = isAfter
        ? ColorResources.positiveColor.withOpacity(0.35)
        : ColorResources.borderColor;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: labelColor,
                fontSize: 9,
                fontWeight: FontWeight.w700,
                letterSpacing: 2.0,
              ),
            ),
            const Spacer(),
            GestureDetector(
              onTap: () {},
              child: Text(
                photoPath == null ? '+ ADD' : 'REPLACE',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        AspectRatio(
          aspectRatio: 3 / 4,
          child: GestureDetector(
            onTap: () {},
            child: Container(
              decoration: BoxDecoration(
                color: ColorResources.blackColor,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: borderColor, width: 0.5),
              ),
              child: photoPath != null
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.asset(
                        photoPath,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => _photoPlaceholder(),
                      ),
                    )
                  : _photoPlaceholder(),
            ),
          ),
        ),
      ],
    );
  }

  Widget _photoPlaceholder() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          Icons.add_a_photo_outlined,
          size: 22,
          color: ColorResources.liteTextColor.withOpacity(0.4),
        ),
        const SizedBox(height: 6),
        Text(
          'TAP TO ADD',
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor.withOpacity(0.4),
            fontSize: 9,
            letterSpacing: 1.5,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  // ── PRODUCT LIST ──────────────────────────────────────
  Widget _buildProductList(
    List<Map<String, dynamic>> products,
    bool isRecommended,
  ) {
    if (products.isEmpty) {
      return _emptyState(
        isRecommended ? Icons.recommend_outlined : Icons.science_outlined,
        isRecommended
            ? 'NO PRODUCTS RECOMMENDED YET.'
            : 'NO PRODUCTS USED YET.',
      );
    }

    return Column(
      children: products.asMap().entries.map((e) {
        final p = e.value;
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
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
                decoration: BoxDecoration(
                  color: isRecommended
                      ? ColorResources.primaryColor
                      : ColorResources.liteTextColor,
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
                onTap: () => setState(() => products.removeAt(e.key)),
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

  // ── NEXT SESSION ──────────────────────────────────────
  Widget _buildNextSession() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Current next session from system
        Row(
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
                size: 16,
                color: ColorResources.primaryColor,
              ),
            ),
            const SizedBox(width: 14),
            const Expanded(
              child: Text(
                _nextSessionLabel,
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
        ),

        const SizedBox(height: 14),
        Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),
        const SizedBox(height: 14),

        // Therapist suggestion field
        Text(
          'THERAPIST NOTE FOR NEXT SESSION',
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.liteTextColor,
            fontSize: 9,
            letterSpacing: 2.0,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        _styledTextField(
          TextEditingController(text: _nextSessionSuggestion),
          'e.g. Focus on décolleté area next session. Bring extra serum.',
          maxLines: 2,
          onChanged: (v) => _nextSessionSuggestion = v,
        ),
      ],
    );
  }

  // ── FIXED SAVE BAR ────────────────────────────────────
  Widget _buildSaveBar() {
    final canSave = _status == 'COMPLETED';
    return Positioned(
      bottom: 0,
      left: 0,
      right: 0,
      child: Container(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        decoration: BoxDecoration(
          color: ColorResources.blackColor.withOpacity(0.85),
          border: Border(
            top: BorderSide(
              color: ColorResources.primaryColor.withOpacity(0.15),
              width: 0.5,
            ),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.4),
              blurRadius: 20,
              offset: const Offset(0, -5),
            ),
          ],
        ),
        child: GestureDetector(
          onTap: canSave
              ? () => _confirmAction(
                    title: 'Save Session?',
                    message:
                        'Save all notes, photos and product data for this session?',
                    confirmLabel: 'SAVE',
                    onConfirm: () {
                      Get.back();
                    },
                  )
              : null,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 18),
            decoration: BoxDecoration(
              gradient: canSave
                  ? LinearGradient(
                      colors: [
                        ColorResources.primaryColor,
                        ColorResources.primaryColor.withValues(alpha: 0.8),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    )
                  : null,
              color: canSave ? null : ColorResources.cardColor,
              borderRadius: BorderRadius.circular(14),
              border: canSave
                  ? null
                  : Border.all(
                      color: ColorResources.primaryColor.withOpacity(0.2),
                      width: 1,
                    ),
              boxShadow: canSave
                  ? [
                      BoxShadow(
                        color: ColorResources.primaryColor.withOpacity(0.3),
                        blurRadius: 15,
                        spreadRadius: 1,
                        offset: const Offset(0, 4),
                      ),
                    ]
                  : [],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  canSave
                      ? Icons.check_circle_outline_rounded
                      : Icons.lock_outline_rounded,
                  size: 18,
                  color: canSave
                      ? Colors.black
                      : ColorResources.liteTextColor.withOpacity(0.3),
                ),
                const SizedBox(width: 10),
                Text(
                  canSave ? 'SAVE & COMPLETE SESSION' : 'COMPLETE SESSION TO SAVE',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: canSave
                        ? Colors.black
                        : ColorResources.liteTextColor.withOpacity(0.3),
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.8,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ─────────────────────────────────────────────────────
  // SHARED WIDGETS
  // ─────────────────────────────────────────────────────

  Widget _buildSectionCard({
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
              if (actionLabel != null) ...[
                const Spacer(),
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
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }

  Widget _emptyState(IconData icon, String message) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 22),
      decoration: BoxDecoration(
        color: ColorResources.blackColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        children: [
          Icon(
            icon,
            size: 22,
            color: ColorResources.liteTextColor.withOpacity(0.35),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.45),
              fontSize: 10,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoCell(
    IconData icon,
    String label,
    String value,
    Color valueColor,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
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
          children: [
            Icon(
              icon,
              size: 12,
              color: ColorResources.liteTextColor.withOpacity(0.45),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                value,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: valueColor,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  height: 1.3,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _labelledBlock(
    String label,
    String value,
    Color color,
    IconData icon,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: color.withOpacity(0.7),
            fontSize: 9,
            fontWeight: FontWeight.w700,
            letterSpacing: 2,
          ),
        ),
        const SizedBox(height: 5),
        Row(
          children: [
            Icon(icon, size: 12, color: color.withOpacity(0.5)),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                value,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: color.withOpacity(0.8),
                  fontSize: 13,
                  fontStyle: FontStyle.italic,
                  height: 1.3,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _styledTextField(
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
          color: ColorResources.whiteColor.withOpacity(0.22),
          fontSize: 13,
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

  Widget _primaryBtn({required String label, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 13),
        decoration: BoxDecoration(
          color: ColorResources.primaryColor,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Text(
            label,
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
    );
  }

  Widget _outlineBtn({required String label, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 13),
        decoration: BoxDecoration(
          color: ColorResources.blackColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Center(
          child: Text(
            label,
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
    );
  }

  // ─────────────────────────────────────────────────────
  // DIALOGS
  // ─────────────────────────────────────────────────────

  void _confirmAction({
    required String title,
    required String message,
    required String confirmLabel,
    required VoidCallback onConfirm,
    bool isDanger = false,
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
                  letterSpacing: 0.5,
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
                    child: _outlineBtn(
                      label: 'CANCEL',
                      onTap: () => Get.back(),
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
                        padding: const EdgeInsets.symmetric(vertical: 13),
                        decoration: BoxDecoration(
                          color: isDanger
                              ? ColorResources.negativeColor
                              : ColorResources.primaryColor,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Center(
                          child: Text(
                            confirmLabel,
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

  void _showNoteDialog({int? index}) {
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
              _styledTextField(titleCtrl, 'Note title...'),
              const SizedBox(height: 12),
              _styledTextField(descCtrl, 'Write details here...', maxLines: 4),
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: _outlineBtn(
                      label: 'CANCEL',
                      onTap: () => Get.back(),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _primaryBtn(
                      label: index != null ? 'UPDATE' : 'SAVE',
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

  void _confirmDeleteNote(int index) {
    _confirmAction(
      title: 'Delete Note?',
      message: 'This note will be permanently removed.',
      confirmLabel: 'DELETE',
      isDanger: true,
      onConfirm: () => setState(() => _notes.removeAt(index)),
    );
  }

  void _showProductPicker({required bool isRecommended}) {
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
                Text(
                  isRecommended ? 'RECOMMEND PRODUCT' : 'ADD PRODUCT USED',
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 2.5,
                  ),
                ),
                const SizedBox(height: 14),

                _styledTextField(
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

                SizedBox(
                  height: 190,
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

                if (selectedProduct != null) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Text(
                        'QTY (${selectedProduct!['unit']})',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor.withOpacity(0.5),
                          fontSize: 9,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 2,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: _styledTextField(
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
                      child: _outlineBtn(
                        label: 'CANCEL',
                        onTap: () => Get.back(),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _primaryBtn(
                        label: 'ADD',
                        onTap: () {
                          if (selectedProduct == null) return;
                          setState(() {
                            final entry = {
                              'name': selectedProduct!['name'],
                              'unit': selectedProduct!['unit'],
                              'quantity': int.tryParse(qtyCtrl.text) ?? 1,
                            };
                          });
                          Get.back();
                        },
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
}

// ── Action Button ──────────────────────────────────────────
class _ActionBtn extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool enabled;
  final bool isPrimary;
  final VoidCallback onTap;

  const _ActionBtn({
    required this.label,
    required this.icon,
    required this.enabled,
    required this.isPrimary,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: enabled ? onTap : null,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          gradient: isPrimary && enabled
              ? LinearGradient(
                  colors: [
                    ColorResources.primaryColor,
                    ColorResources.primaryColor.withValues(alpha: 0.8),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : null,
          color: isPrimary
              ? (enabled ? null : ColorResources.primaryColor.withOpacity(0.08))
              : (enabled
                  ? ColorResources.cardColor
                  : ColorResources.cardColor.withOpacity(0.5)),
          borderRadius: BorderRadius.circular(12),
          border: isPrimary
              ? (enabled
                  ? null
                  : Border.all(
                      color: ColorResources.primaryColor.withOpacity(0.15),
                      width: 1,
                    ))
              : Border.all(
                  color: enabled
                      ? ColorResources.primaryColor.withOpacity(0.4)
                      : ColorResources.borderColor,
                  width: 1,
                ),
          boxShadow: isPrimary && enabled
              ? [
                  BoxShadow(
                    color: ColorResources.primaryColor.withOpacity(0.25),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ]
              : null,
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 16,
              color: isPrimary
                  ? (enabled
                      ? Colors.black
                      : ColorResources.primaryColor.withOpacity(0.3))
                  : (enabled
                      ? ColorResources.primaryColor
                      : ColorResources.primaryColor.withOpacity(0.3)),
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: isPrimary
                    ? (enabled
                        ? Colors.black
                        : ColorResources.primaryColor.withOpacity(0.3))
                    : (enabled
                        ? ColorResources.primaryColor
                        : ColorResources.primaryColor.withOpacity(0.3)),
                fontSize: 13,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Status Badge ───────────────────────────────────────────
class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge({required this.status});

  Color get _color {
    switch (status) {
      case 'COMPLETED':
        return const Color(0xFF5C7A5C);
      case 'IN SESSION':
        return ColorResources.primaryColor;
      default:
        return const Color(0xFF6A6A6A);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: _color.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              color: _color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            status,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: _color,
              fontSize: 10,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
