import 'package:aura/app/page/admin/patient/view/widgets/consent_tab.dart';
import 'package:aura/app/page/admin/patient/view/widgets/history_tab.dart';
import 'package:aura/app/page/admin/patient/view/widgets/notes_tab.dart';
import 'package:aura/app/page/admin/patient/view/widgets/photos_tab.dart';
import 'package:aura/app/widgets/app_tab_view.dart';
import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';
import '../../../../theme/color/color.dart';
import '../cubit/patient_detail_cubit.dart';
import '../model/patient_model.dart';
import 'widgets/personal_tab.dart';

class PatientDetailScreen extends StatelessWidget {
  const PatientDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final patient = Get.arguments as PatientModel? ?? const PatientModel(
      id: '',
      name: 'Unknown',
      phone: '',
      image: '',
    );

    return BlocProvider(
      create: (_) => PatientDetailCubit(),
      child: _PatientDetailBody(patient: patient),
    );
  }
}

// ── BODY ───────────────────────────────────────────────────
class _PatientDetailBody extends StatelessWidget {
  final PatientModel patient;
  const _PatientDetailBody({required this.patient});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: CustomAppBar(title: 'PATIENT DETAILS'),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 16),

              // ── Avatar ──────────────────────────────────
              Center(
                child: Container(
                  padding: const EdgeInsets.all(3),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: ColorResources.primaryColor,
                      width: 2,
                    ),
                  ),
                  child: CircleAvatar(
                    radius: 68,
                    backgroundColor: ColorResources.cardColor,
                    backgroundImage: patient.image.isNotEmpty
                        ? NetworkImage(patient.image)
                        : const NetworkImage(
                            'https://i.pinimg.com/1200x/8d/51/16/8d5116e7e8f31b64a9ca530bef7a087e.jpg',
                          ),
                    onBackgroundImageError: (_, __) {},
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // ── Name ────────────────────────────────────
              Center(
                child: Text(
                  patient.name,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 30,
                    fontWeight: FontWeight.w300,
                    fontStyle: FontStyle.italic,
                    letterSpacing: 0.5,
                  ),
                ),
              ),

              const SizedBox(height: 6),

              // ── Patient ID ──────────────────────────────
              Center(
                child: RichText(
                  text: TextSpan(
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      fontSize: 11,
                      letterSpacing: 2.0,
                      color: ColorResources.liteTextColor,
                      fontWeight: FontWeight.w600,
                    ),
                    children: [
                      const TextSpan(text: 'PATIENT ID: '),
                      TextSpan(
                        text: '#${patient.id}',
                        style: const TextStyle(
                          color: ColorResources.primaryColor,
                          fontStyle: FontStyle.italic,
                          fontWeight: FontWeight.w400,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 14),

              // ── Patient Tags ─────────────────────────────
              const _PatientTags(),

              const SizedBox(height: 14),
// Below _PatientTags(), above tabs
_PatientStatStrip(patient: patient),

  const SizedBox(height: 24),
              // ── Tabs + Content ──────────────────────────
              BlocBuilder<PatientDetailCubit, PatientDetailState>(
                builder: (context, state) {
                  return AppTabView(
                    selectedTab: state.selectedTab,
                    onTabChanged: (i) =>
                        context.read<PatientDetailCubit>().selectTab(i),
                    tabs: const [
                      'PERSONAL',
                      'HISTORY',
                      'NOTES',
                      'PHOTOS',
                      'CONSENT',
                    ],
                    children: [
                      PersonalTab(patient: patient),
                      const HistoryTab(),
                      const NotesTab(),
                      const PhotosTab(),
                      const ConsentTab(),
                    ],
                  );
                },
              ),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}

// ── PATIENT TAGS ───────────────────────────────────────────
class _PatientTags extends StatelessWidget {
  const _PatientTags();

  @override
  Widget build(BuildContext context) {
    return Center(child: _TagChip(label: 'VIP MEMBER'));
  }
}

class _TagChip extends StatelessWidget {
  final String label;
  const _TagChip({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      decoration: BoxDecoration(
        color: ColorResources.primaryColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: ColorResources.primaryColor, width: 0.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 2.0,
              color: ColorResources.liteTextColor,
            ),
          ),
        ],
      ),
    );
  }
}


class _PatientStatStrip extends StatelessWidget {
  final PatientModel patient;
  const _PatientStatStrip({required this.patient});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Row(
          children: [
            _stat('6', 'VISITS'),
            _divider(),
            _stat('10 Mar', 'LAST VISIT'),
            _divider(),
            _stat('\$850', 'TOTAL SPENT'),
          ],
        ),
      ),
    );
  }

  Widget _stat(String value, String label) => Expanded(
    child: Column(children: [
      Text(value, style: TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.primaryColor,
        fontSize: 18, fontWeight: FontWeight.w600,
      )),
      const SizedBox(height: 2),
      Text(label, style: TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.liteTextColor,
        fontSize: 9, letterSpacing: 1.5, fontWeight: FontWeight.w600,
      )),
    ]),
  );

  Widget _divider() => Container(
    width: 0.5, height: 32, color: ColorResources.borderColor);
}