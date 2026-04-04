import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:flutter/material.dart';

import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/primary_button.dart';
import '../../../../widgets/secondary_button.dart';

class AppointmentDetailScreen extends StatefulWidget {
  const AppointmentDetailScreen({super.key});

  @override
  State<AppointmentDetailScreen> createState() =>
      _AppointmentDetailScreenState();
}

class _AppointmentDetailScreenState extends State<AppointmentDetailScreen> {
  String _status = 'UPCOMING';

  static const _patient = 'Isabelle Morel';
  static const _time = '11:45 AM';
  static const _date = 'Oct 24, 2024';
  static const _phone = '+91 98765 43210';
  static const _email = 'isabelle.morel@email.com';
  static const _gender = 'Female';
  static const _age = '34';
  static const _treatment = 'Hydra-Facial Platinum';
  static const _duration = '45 mins';
  static const _treatmentNotes = 'Sensitive skin — avoid retinol products.';
  static const _therapist = 'Sarah Jenkins';
  static const _room = 'Facial Room 1';
  static const _receptionistNotes =
      'Patient prefers evening slots. First-time client — extra consultation needed before session.';
  static const _paymentStatus = 'PENDING';
  static const _paymentAmount = '\$310.00';
  static const _lastVisitDate = 'Oct 10, 2024';
  static const _lastVisitTreatment = 'Deep Cleanse Facial';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: CustomAppBar(title: 'APPOINTMENT DETAIL'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 140),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeroSection(),
            const SizedBox(height: 16),

            _buildPatientSection(),
            const SizedBox(height: 14),

            _buildSection(
              label: 'TREATMENT',
              child: _buildTreatmentDetails(),
            ),
            const SizedBox(height: 14),

            // 4️⃣ Therapist & Room
            _buildSection(
              label: 'THERAPIST & ROOM',
              child: _buildTherapistRoom(),
            ),
            const SizedBox(height: 14),
    _buildSection(
              label: 'CONSENT',
              child: _buildConsent(),
            ),
            const SizedBox(height: 14),
            // 5️⃣ Notes
            _buildSection(label: 'NOTES', child: _buildNotes()),
            const SizedBox(height: 14),

            // 6️⃣ Payment
            _buildSection(label: 'PAYMENT', child: _buildPayment()),
            const SizedBox(height: 14),

            // 7️⃣ History
            _buildSection(label: 'LAST VISIT', child: _buildHistory()),
          ],
        ),
      ),
      bottomNavigationBar: _buildActionButtons(),
    );
  }



         

  // ── 1️⃣ Hero Section ──────────────────────────────────
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
          // ── Centered Avatar ──
          Container(
            padding: const EdgeInsets.all(3),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(
                  color: ColorResources.primaryColor, width: 2),
            ),
            child: const CircleAvatar(
              radius: 52,
              backgroundColor: Color(0xFF1A1A1A),
              child: Icon(Icons.person,
                  color: ColorResources.liteTextColor, size: 48),
            ),
          ),

          const SizedBox(height: 18),

          // ── Patient Name ──
          Text(
            _patient,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 28,
              fontWeight: FontWeight.w300,
              fontStyle: FontStyle.italic,
              letterSpacing: 1.0,
            ),
          ),

          const SizedBox(height: 6),

          // ── Time · Date ──
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.access_time_rounded,
                  size: 12, color: ColorResources.primaryColor),
              const SizedBox(width: 5),
              Text(
                '$_time  ·  $_date',
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.8,
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // ── Status Badge ──
          _buildStatusBadge(_status),
        ],
      ),
    );
  }

  // ── 2️⃣ Patient Details Section ───────────────────────
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
          // Section label
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 18, 18, 14),
            child: const Text(
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

          // Phone number — large display
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 0),
            child: Text(
              _phone,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 22,
                fontWeight: FontWeight.w400,
                letterSpacing: 1.5,
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Call Patient button — full width gold
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
            child: GestureDetector(
              onTap: () {},
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 16),
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

          // Divider
          Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5),

          // Email + Gender + Age
          Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              children: [
                _infoRow(Icons.email_outlined, 'Email', _email),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                        child: _infoRow(
                            Icons.person_outlined, 'Gender', _gender)),
                    const SizedBox(width: 20),
                    Expanded(
                        child: _infoRow(
                            Icons.cake_outlined, 'Age', '$_age yrs')),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── 3️⃣ Treatment ─────────────────────────────────────
  Widget _buildTreatmentDetails() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          _treatment,
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 18,
            fontWeight: FontWeight.w500,
            letterSpacing: 0.3,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            const Icon(Icons.timer_outlined,
                size: 13, color: ColorResources.liteTextColor),
            const SizedBox(width: 6),
            Text('Duration: $_duration',
                style: AppTextStyles.bodyItalic.copyWith(fontSize: 13)),
          ],
        ),
        const SizedBox(height: 14),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: ColorResources.blackColor,
            borderRadius: BorderRadius.circular(8),
            border:
                Border.all(color: ColorResources.borderColor, width: 0.5),
          ),
          child: Text(_treatmentNotes,
              style: AppTextStyles.bodyItalic.copyWith(fontSize: 12)),
        ),
      ],
    );
  }

  // ── 4️⃣ Therapist & Room ──────────────────────────────
  Widget _buildTherapistRoom() {
    return Row(
      children: [
        Expanded(
            child:
                _infoRow(Icons.person_outline, 'Therapist', _therapist)),
        const SizedBox(width: 20),
        Expanded(
            child: _infoRow(
                Icons.meeting_room_outlined, 'Room', _room)),
      ],
    );
  }

  // ── 5️⃣ Notes ─────────────────────────────────────────
  Widget _buildNotes() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: ColorResources.blackColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Text(_receptionistNotes,
          style: AppTextStyles.bodyItalic.copyWith(fontSize: 13)),
    );
  }
 // ── 4️⃣ Therapist & Room ──────────────────────────────
static const _consentStatus = 'PENDING'; // 'SIGNED' | 'PENDING' | 'MISSING'
 
  Widget _buildConsent() {
    // ── Resolve colors + label from status ──────────────
    Color dotColor;
    Color labelColor;
    String statusLabel;
    String subLabel;
    IconData statusIcon;
 
    switch (_consentStatus) {
      case 'SIGNED':
        dotColor    = const Color(0xFF5C7A5C);
        labelColor  = const Color(0xFF5C7A5C);
        statusLabel = 'SIGNED';
        subLabel    = 'Consent form on file';
        statusIcon  = Icons.check_circle_outline;
        break;
      case 'MISSING':
        dotColor    = ColorResources.negativeColor;
        labelColor  = ColorResources.negativeColor;
        statusLabel = 'MISSING';
        subLabel    = 'No consent form recorded';
        statusIcon  = Icons.error_outline;
        break;
      default: // PENDING
        dotColor    = ColorResources.primaryColor;
        labelColor  = ColorResources.primaryColor;
        statusLabel = 'PENDING';
        subLabel    = 'Awaiting signed form';
        statusIcon  = Icons.radio_button_unchecked;
    }
 
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Status row ───────────────────────────────
        Row(
          children: [
            // Dot
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: dotColor,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 10),
 
            // Status label
            Text(
              statusLabel,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: labelColor,
                fontSize: 13,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.5,
              ),
            ),
 
            const SizedBox(width: 8),
 
            // Sub label
            Text(
              '· $subLabel',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor,
                fontSize: 13,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
 
        const SizedBox(height: 14),
 
        // ── Action row ───────────────────────────────
        // Shows 'View Form' when SIGNED, 'Upload Form' when PENDING/MISSING
        GestureDetector(
          onTap: () {
            // Navigate to Patient Detail, open CONSENT tab (index 4)
            // Get.toNamed(PageRoutes.patientDetailScreen,
            //   arguments: patient,
            //   parameters: {'tab': '4'},
            // );
          },
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 13),
            decoration: BoxDecoration(
              color: _consentStatus == 'SIGNED'
                  ? Colors.transparent
                  : ColorResources.primaryColor.withOpacity(0.06),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: _consentStatus == 'SIGNED'
                    ? ColorResources.borderColor
                    : ColorResources.primaryColor.withOpacity(0.4),
                width: 0.5,
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  _consentStatus == 'SIGNED'
                      ? Icons.picture_as_pdf_outlined
                      : Icons.upload_file_outlined,
                  color: _consentStatus == 'SIGNED'
                      ? ColorResources.liteTextColor
                      : ColorResources.primaryColor,
                  size: 14,
                ),
                const SizedBox(width: 8),
                Text(
                  _consentStatus == 'SIGNED'
                      ? 'VIEW CONSENT FORM'
                      : 'UPLOAD CONSENT FORM',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: _consentStatus == 'SIGNED'
                        ? ColorResources.liteTextColor
                        : ColorResources.primaryColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 2.0,
                  ),
                ),
                const SizedBox(width: 6),
                Icon(
                  Icons.arrow_forward_ios,
                  color: _consentStatus == 'SIGNED'
                      ? ColorResources.liteTextColor
                      : ColorResources.primaryColor,
                  size: 10,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
 
  // ── 6️⃣ Payment ───────────────────────────────────────
  Widget _buildPayment() {
    final bool isPaid = _paymentStatus == 'PAID';
    final Color payColor = isPaid
        ? const Color(0xFF5C7A5C)
        : ColorResources.primaryColor;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          _paymentAmount,
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 22,
            fontWeight: FontWeight.w400,
            letterSpacing: 0.5,
          ),
        ),
        Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
          decoration: BoxDecoration(
            color: payColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(5),
            border:
                Border.all(color: payColor.withOpacity(0.35), width: 0.5),
          ),
          child: Text(
            _paymentStatus,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: payColor,
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
            ),
          ),
        ),
      ],
    );
  }

  // ── 7️⃣ History ───────────────────────────────────────
  Widget _buildHistory() {
    return Row(
      children: [
        const Icon(Icons.history_rounded,
            size: 14, color: ColorResources.liteTextColor),
        const SizedBox(width: 8),
        Text(
          '$_lastVisitDate  ·  $_lastVisitTreatment',
          style: AppTextStyles.bodyItalic.copyWith(fontSize: 13),
        ),
      ],
    );
  }

  // ── Action Buttons ────────────────────────────────────
  Widget _buildActionButtons() {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 36),
      decoration: BoxDecoration(
        color: ColorResources.blackColor,
        border: Border(
            top: BorderSide(
                color: ColorResources.borderColor, width: 0.5)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Expanded(
                child: SecondaryButton(
                  onTap: () {}, 
                  title: "CANCEL",
                  height: 48,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: PrimaryButton(
                  label: "RESCHEDULE", 
                  onTap: () {},
                  height: 48,
                ),
              )
            ],
          ),
        ],
      ),
    );
  }

  // ── Section Card ──────────────────────────────────────
  Widget _buildSection({required String label, required Widget child}) {
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
          children: [
            Icon(icon,
                size: 13,
                color: ColorResources.liteTextColor.withOpacity(0.5)),
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
        color = ColorResources.positiveColor;
        break;
      case 'IN SESSION':
        color = ColorResources.primaryColor;
        break;
      case 'CANCELLED':
        color =  ColorResources.negativeColor;
        break;
      case 'ARRIVED':
        color = ColorResources.blueColor;
        break;
      default:
        color = ColorResources.blueColor;
    }

    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
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