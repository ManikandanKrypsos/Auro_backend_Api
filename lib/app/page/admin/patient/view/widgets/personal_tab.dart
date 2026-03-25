import 'package:flutter/material.dart';

import '../../../../../theme/color/color.dart';
import 'pateint_personal_detail_widgets.dart';
import '../../model/patient_model.dart';

class PersonalTab extends StatelessWidget {
  final PatientModel patient;
  const PersonalTab({super.key, required this.patient});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── CONTACT DETAILS ──────────────────────────────
        SectionHeader(label: 'CONTACT DETAILS'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            children: [
              ContactCard(
                icon: Icons.mail_outline,
                label: 'EMAIL',
                value: patient.email.isNotEmpty ? patient.email : '-',
              ),
              const SizedBox(height: 10),
              ContactCard(
                icon: Icons.phone_outlined,
                label: 'PHONE',
                value: patient.phone.isNotEmpty ? patient.phone : '-',
              ),
            ],
          ),
        ),

        const SizedBox(height: 32),

        // ── ADDRESS ──────────────────────────────────────
        SectionHeader(label: 'ADDRESS'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Container(
            decoration: BoxDecoration(
              color: ColorResources.cardColor,
              borderRadius: BorderRadius.circular(10),
              border:
                  Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Column(
              children: [
                MedicalRow(
                  label: 'CITY',
                  value: patient.city.isNotEmpty ? patient.city : '-',
                  valueColor: ColorResources.whiteColor,
                ),
                _divider(),
                MedicalRow(
                  label: 'COUNTRY',
                  value: patient.country.isNotEmpty ? patient.country : '-',
                  valueColor: ColorResources.whiteColor,
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 32),

        // ── BASIC INFORMATION ────────────────────────────
        SectionHeader(label: 'BASIC INFORMATION'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Container(
            decoration: BoxDecoration(
              color: ColorResources.cardColor,
              borderRadius: BorderRadius.circular(10),
              border:
                  Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Column(
              children: [
                MedicalRow(
                  label: 'GENDER',
                  value: patient.gender.isNotEmpty ? patient.gender : '-',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
                _divider(),
                MedicalRow(
                  label: 'DATE OF BIRTH',
                  value: patient.dob.isNotEmpty ? patient.dob : '-',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
                _divider(),
                MedicalRow(
                  label: 'AGE',
                  value: _calculateAge(patient.dob),
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 32),

        // ── MEDICAL SUMMARY ──────────────────────────────
        SectionHeader(label: 'MEDICAL SUMMARY'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Container(
            decoration: BoxDecoration(
              color: ColorResources.cardColor,
              borderRadius: BorderRadius.circular(10),
              border:
                  Border.all(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Column(
              children: [
                MedicalRow(
                  label: 'BLOOD TYPE',
                  value: patient.bloodType.isNotEmpty ? patient.bloodType : '-',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
                _divider(),
                MedicalRow(
                 label: 'ALLERGIES',
                  value: patient.allergies.isNotEmpty ? patient.allergies : 'None',
                  valueColor: ColorResources.primaryColor,
                  isItalic: true,
                ),
                _divider(),
                MedicalRow(
                  label: 'SKIN TYPE',
                  value: patient.skinType.isNotEmpty ? patient.skinType : '-',
                  valueColor: ColorResources.negativeColor,
                  isItalic: true,
                ),
                _divider(),
                MedicalRow(
                  label: 'CONTRAINDICATIONS',
                  value: patient.contraindications.isNotEmpty ? patient.contraindications : 'None',
                  valueColor: ColorResources.negativeColor,
                  isItalic: true,
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 32),

        // ── MARKETING SOURCE ─────────────────────────────
        SectionHeader(label: 'MARKETING SOURCE'),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              SourceChip(label: 'Instagram', icon: Icons.photo_camera_outlined, isSelected: patient.marketingSource.toLowerCase() == 'instagram'),
              SourceChip(label: 'Website', icon: Icons.language_outlined, isSelected: patient.marketingSource.toLowerCase() == 'website'),
              SourceChip(label: 'Walk-in', icon: Icons.directions_walk_outlined, isSelected: patient.marketingSource.toLowerCase() == 'walk-in'),
              SourceChip(label: 'Referral', icon: Icons.people_outline, isSelected: patient.marketingSource.toLowerCase() == 'referral'),
            ],
          ),
        ),

        const SizedBox(height: 24),
      ],
    );
  }

  Widget _divider() =>
      Divider(color: ColorResources.borderColor, height: 1, thickness: 0.5);

  String _calculateAge(String dob) {
    if (dob.isEmpty) return '-';
    try {
      // Extract a 4-digit year starting with 19 or 20
      final yearMatch = RegExp(r'\b(19|20)\d{2}\b').firstMatch(dob);
      if (yearMatch != null) {
        int birthYear = int.parse(yearMatch.group(0)!);
        int currentYear = DateTime.now().year;
        int age = currentYear - birthYear;
        if (age >= 0 && age <= 120) {
          return age.toString();
        }
      }
      return '-';
    } catch (e) {
      return '-';
    }
  }
}

