import 'package:flutter/material.dart';
import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

class ConsentTab extends StatelessWidget {
  const ConsentTab({super.key});

  // ── Open upload bottom sheet ─────────────────────────
  void _showUploadSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _ConsentUploadSheet(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Summary strip ────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              color: ColorResources.cardColor,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Row(
              children: [
                _summaryCell('3', 'SIGNED'),
                Container(
                  width: 0.5,
                  height: 36,
                  color: ColorResources.borderColor,
                ),
                _summaryCell('1', 'PENDING'),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // ── Add button ───────────────────────────────
          GestureDetector(
            onTap: () => _showUploadSheet(context),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 14),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: ColorResources.primaryColor.withOpacity(0.4),
                  width: 0.5,
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.add, color: ColorResources.primaryColor, size: 14),
                  const SizedBox(width: 8),
                  Text(
                    'ADD CONSENT FORM',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.0,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          Text(
            'CONSENT RECORDS',
            style: AppTextStyles.headingSmall.copyWith(
              fontSize: 11,
              color: ColorResources.liteTextColor,
              letterSpacing: 3.5,
            ),
          ),

          const SizedBox(height: 16),

          _card(
            title: 'General Treatment Consent',
            date: '12 Jan 2025',
            file: 'general_consent_jan25.pdf',
            isSigned: true,
            patientSigned: true,
            therapistConfirmed: true,
          ),
          _card(
            title: 'Photography & Media Release',
            date: '12 Jan 2025',
            file: 'media_release_jan25.pdf',
            isSigned: true,
            patientSigned: true,
            therapistConfirmed: true,
          ),
          _card(
            title: 'Dermapen Consent',
            date: '10 Mar 2025',
            file: 'dermapen_consent_mar25.pdf',
            isSigned: true,
            patientSigned: true,
            therapistConfirmed: true,
          ),
          _card(
            title: 'Chemical Peel Consent',
            date: '—',
            file: 'chemical_peel_consent.pdf',
            isSigned: false,
            patientSigned: false,
            therapistConfirmed: false,
          ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _summaryCell(String value, String label) {
    return Expanded(
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.primaryColor,
              fontSize: 22,
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
    );
  }

  Widget _card({
    required String title,
    required String date,
    required String file,
    required bool isSigned,
    required bool patientSigned,
    required bool therapistConfirmed,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
            child: Row(
              children: [
                Icon(
                  isSigned
                      ? Icons.check_circle_outline
                      : Icons.radio_button_unchecked,
                  color: isSigned
                      ? ColorResources.primaryColor
                      : ColorResources.liteTextColor,
                  size: 18,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor,
                          fontSize: 15,
                          fontWeight: FontWeight.w400,
                          letterSpacing: 0.3,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        isSigned ? 'Signed — $date' : 'Awaiting signature',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor,
                          fontSize: 11,
                          fontStyle: FontStyle.italic,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                ),
                Text(
                  isSigned ? 'SIGNED' : 'PENDING',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: isSigned
                        ? ColorResources.primaryColor
                        : ColorResources.liteTextColor,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.5,
                  ),
                ),
              ],
            ),
          ),
          Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 12),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: ColorResources.blackColor,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: ColorResources.borderColor,
                      width: 0.5,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.picture_as_pdf_outlined,
                        color: ColorResources.liteTextColor,
                        size: 12,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        file,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor.withOpacity(0.5),
                          fontSize: 11,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                _badge('Patient', patientSigned),
                const SizedBox(width: 12),
                _badge('Therapist', therapistConfirmed),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _badge(String label, bool confirmed) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          confirmed ? Icons.check : Icons.close,
          size: 11,
          color: confirmed
              ? ColorResources.primaryColor
              : ColorResources.liteTextColor,
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: confirmed
                ? ColorResources.whiteColor.withOpacity(0.6)
                : ColorResources.liteTextColor,
            fontSize: 11,
            letterSpacing: 0.3,
          ),
        ),
      ],
    );
  }
}

// ── Upload Bottom Sheet ────────────────────────────────────
class _ConsentUploadSheet extends StatefulWidget {
  const _ConsentUploadSheet();

  @override
  State<_ConsentUploadSheet> createState() => _ConsentUploadSheetState();
}

class _ConsentUploadSheetState extends State<_ConsentUploadSheet> {
  String _selectedFormType = 'General Treatment Consent';
  String _selectedDate = 'Apr 2, 2026';
  bool _isPatientSigned = false;
  bool _isTherapistSigned = false;

  static const _formTypes = [
    'General Treatment Consent',
    'Photography & Media Release',
    'Dermapen Consent',
    'Chemical Peel Consent',
    'Laser Treatment Consent',
    'Crystal Frax Consent',
    'Other',
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF111111),
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // ── Handle ──────────────────────────────────
          const SizedBox(height: 12),
          Center(
            child: Container(
              width: 36,
              height: 3,
              decoration: BoxDecoration(
                color: ColorResources.borderColor,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),

          // ── Title ────────────────────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'ADD CONSENT FORM',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 2.5,
                  ),
                ),
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Icon(
                    Icons.close,
                    color: ColorResources.liteTextColor,
                    size: 18,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20),
          Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),
          const SizedBox(height: 20),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Form Type ────────────────────────────
                _fieldLabel('FORM TYPE'),
                const SizedBox(height: 8),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: ColorResources.cardColor,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: ColorResources.borderColor,
                      width: 0.5,
                    ),
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: _selectedFormType,
                      dropdownColor: const Color(0xFF1A1A1A),
                      isExpanded: true,
                      style: const TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 14,
                        letterSpacing: 0.3,
                      ),
                      items: _formTypes
                          .map(
                            (t) => DropdownMenuItem(value: t, child: Text(t)),
                          )
                          .toList(),
                      onChanged: (v) {
                        if (v != null) setState(() => _selectedFormType = v);
                      },
                    ),
                  ),
                ),

                const SizedBox(height: 18),

                // ── Date Signed ──────────────────────────
                _fieldLabel('DATE SIGNED'),
                const SizedBox(height: 8),
                GestureDetector(
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: DateTime.now(),
                      firstDate: DateTime(2020),
                      lastDate: DateTime.now(),
                      builder: (context, child) => Theme(
                        data: ThemeData.dark().copyWith(
                          colorScheme: ColorScheme.dark(
                            primary: ColorResources.primaryColor,
                            surface: const Color(0xFF1A1A1A),
                          ),
                        ),
                        child: child!,
                      ),
                    );
                    if (picked != null) {
                      setState(() {
                        _selectedDate =
                            '${picked.day} ${_monthName(picked.month)} ${picked.year}';
                      });
                    }
                  },
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 14,
                    ),
                    decoration: BoxDecoration(
                      color: ColorResources.cardColor,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: ColorResources.borderColor,
                        width: 0.5,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.calendar_today_outlined,
                          color: ColorResources.primaryColor,
                          size: 14,
                        ),
                        const SizedBox(width: 10),
                        Text(
                          _selectedDate,
                          style: const TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.whiteColor,
                            fontSize: 14,
                            letterSpacing: 0.3,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 18),

                // ── Upload zone ──────────────────────────
                _fieldLabel('ATTACH CONSENT PDF'),
                const SizedBox(height: 8),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 28),
                  decoration: BoxDecoration(
                    color: ColorResources.cardColor,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: ColorResources.primaryColor.withOpacity(0.25),
                      width: 0.5,
                    ),
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.picture_as_pdf_outlined,
                        color: ColorResources.primaryColor.withOpacity(0.5),
                        size: 28,
                      ),
                      const SizedBox(height: 10),
                      Text(
                        'TAP TO SELECT PDF',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.primaryColor,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 2.0,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'PDF only · max 10 MB',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor,
                          fontSize: 11,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // ── Signature Status ─────────────────────
                _fieldLabel('SIGNATURE STATUS'),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _signatureToggle(
                      label: 'Patient Signed',
                      isSelected: _isPatientSigned,
                      onTap: () => setState(() => _isPatientSigned = !_isPatientSigned),
                    ),
                    const SizedBox(width: 12),
                    _signatureToggle(
                      label: 'Therapist Signed',
                      isSelected: _isTherapistSigned,
                      onTap: () => setState(() => _isTherapistSigned = !_isTherapistSigned),
                    ),
                  ],
                ),


    const SizedBox(height: 12),
                // ── Save button ──────────────────────────
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    decoration: BoxDecoration(
                      color: ColorResources.primaryColor,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Center(
                      child: Text(
                        'SAVE CONSENT FORM',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: Colors.black,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 2.5,
                        ),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 32),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Signature toggle option ────────────────────────
  Widget _signatureToggle({
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
          decoration: BoxDecoration(
            color: isSelected
                ? ColorResources.primaryColor.withOpacity(0.1)
                : ColorResources.cardColor,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: isSelected
                  ? ColorResources.primaryColor
                  : ColorResources.borderColor,
              width: isSelected ? 1.0 : 0.5,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                isSelected ? Icons.check_circle : Icons.radio_button_unchecked,
                color: isSelected
                    ? ColorResources.primaryColor
                    : ColorResources.liteTextColor,
                size: 16,
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: isSelected
                      ? ColorResources.whiteColor
                      : ColorResources.liteTextColor,
                  fontSize: 11,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                  letterSpacing: 0.3,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _fieldLabel(String label) {
    return Text(
      label,
      style: TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.liteTextColor,
        fontSize: 9,
        fontWeight: FontWeight.w600,
        letterSpacing: 2.0,
      ),
    );
  }

  String _monthName(int month) {
    const months = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];
    return months[month - 1];
  }
}
