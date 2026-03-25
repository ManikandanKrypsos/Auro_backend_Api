import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:aura/app/widgets/custom_textform_lables.dart';
import 'package:aura/app/widgets/custom_textformfeild.dart';
import 'package:aura/app/widgets/profile_add_widget.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';
import '../../../../theme/color/color.dart';
import '../cubit/add_patient_cubit.dart';
import '../model/patient_model.dart';
import 'widgets/add_edit_patient_widgets.dart';


// ── Screen ─────────────────────────────────────────────────
class AddPatientScreen extends StatelessWidget {
  final bool isedit;
  final PatientModel? patient;
  const AddPatientScreen({super.key, this.isedit = false, this.patient});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => AddPatientCubit(),
      child: BlocListener<AddPatientCubit, AddPatientState>(
        listenWhen: (prev, curr) => prev.status != curr.status,
        listener: (context, state) {
          if (state.status == AddPatientStatus.loading) {
            showDialog(
              context: context,
              barrierDismissible: false,
              builder: (_) => const Center(
                  child: CircularProgressIndicator(
                      color: ColorResources.primaryColor)),
            );
          } else if (state.status == AddPatientStatus.success) {
            Navigator.pop(context); // close dialog
            Get.snackbar("Success", "Patient added successfully!",
                backgroundColor: ColorResources.positiveColor);
            Navigator.pop(context); // go back
          } else if (state.status == AddPatientStatus.error) {
            Navigator.pop(context); // close dialog
            Get.snackbar("Error", state.errorMessage,
                backgroundColor: Colors.white, colorText: ColorResources.negativeColor);
          }
        },
        child: _AddPatientBody(isedit: isedit, patient: patient),
      ),
    );
  }
}

// ── Body ───────────────────────────────────────────────────
class _AddPatientBody extends StatefulWidget {
  final bool isedit;
  final PatientModel? patient;
   const _AddPatientBody({required this.isedit, this.patient});

  @override
  State<_AddPatientBody> createState() => _AddPatientBodyState();
}

class _AddPatientBodyState extends State<_AddPatientBody> {
  final _nameCtrl      = TextEditingController();
  final _emailCtrl     = TextEditingController();
  final _phoneCtrl     = TextEditingController();
  final _cityCtrl      = TextEditingController();
  final _countryCtrl   = TextEditingController();
  final _dobCtrl       = TextEditingController();
  final _bloodTypeCtrl = TextEditingController();
  final _allergiesCtrl = TextEditingController();
  final _contrCtrl     = TextEditingController();

  @override
  void initState() {
    super.initState();
    if (widget.isedit && widget.patient != null) {
      final p = widget.patient!;
      _nameCtrl.text = p.name;
      _emailCtrl.text = p.email;
      _phoneCtrl.text = p.phone;
      _cityCtrl.text = p.city;
      _countryCtrl.text = p.country;
      _dobCtrl.text = p.dob;
      _bloodTypeCtrl.text = p.bloodType;
      _allergiesCtrl.text = p.allergies;
      _contrCtrl.text = p.contraindications;
      
      WidgetsBinding.instance.addPostFrameCallback((_) {
        // Because context is not safe to read Cubit synchronously in initState
        final cubit = context.read<AddPatientCubit>();
        if (p.gender.isNotEmpty) cubit.selectGender(p.gender);
        if (p.skinType.isNotEmpty) cubit.selectSkinType(p.skinType);
        if (p.marketingSource.isNotEmpty) cubit.selectMarketingSource(p.marketingSource);
      });
    }
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    _cityCtrl.dispose();
    _countryCtrl.dispose();
    _dobCtrl.dispose();
    _bloodTypeCtrl.dispose();
    _allergiesCtrl.dispose();
    _contrCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: CustomAppBar(title:widget. isedit? 'EDIT PATIENT': 'ADD NEW PATIENT'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 40),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // ── Avatar ───────────────────────────────────
            const Center(child: ProfileAddWidget()),
            const SizedBox(height: 12),

            // ── CONTACT DETAILS ──────────────────────────
            SectionHeader(icon: Icons.person_outline, text: 'CONTACT DETAILS'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'FULL NAME'),
                  CustomTextField(
                      controller: _nameCtrl, hint: 'Eleanor Vance'),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'EMAIL'),
                  CustomTextField(
                      controller: _emailCtrl,
                      hint: 'e.vance@email.com',
                      keyboardType: TextInputType.emailAddress),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'PHONE'),
                  CustomTextField(
                      controller: _phoneCtrl,
                      hint: '+1 (555) 000-0000',
                      keyboardType: TextInputType.phone),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── ADDRESS ──────────────────────────────────
            SectionHeader(icon: Icons.location_on_outlined, text: 'ADDRESS'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'CITY'),
                  CustomTextField(
                      controller: _cityCtrl, hint: 'New York'),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'COUNTRY'),
                  CustomTextField(
                      controller: _countryCtrl, hint: 'United States'),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── BASIC INFORMATION ─────────────────────────
            SectionHeader(icon: Icons.info_outline, text: 'BASIC INFORMATION'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'GENDER'),
                  const SizedBox(height: 4),
                  const GenderSelector(),
                  const SizedBox(height: 20),
                  const CustomLabel(text: 'DATE OF BIRTH'),
                  CustomTextField(
                      controller: _dobCtrl,
                      hint: '24 April 2000',
                      keyboardType: TextInputType.datetime),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── MEDICAL SUMMARY ───────────────────────────
            SectionHeader(
                icon: Icons.medical_services_outlined,
                text: 'MEDICAL SUMMARY'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const CustomLabel(text: 'BLOOD TYPE'),
                  CustomTextField(
                      controller: _bloodTypeCtrl, hint: 'O Positive'),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'ALLERGIES'),
                  CustomTextField(
                      controller: _allergiesCtrl,
                      hint: 'Penicillin, Latex'),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'SKIN TYPE'),
                  const SkinTypeDropdown(),
                  const SizedBox(height: 14),
                  const CustomLabel(text: 'CONTRAINDICATIONS'),
                  CustomTextField(
                      controller: _contrCtrl, hint: 'None'),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // ── MARKETING SOURCE ──────────────────────────
            SectionHeader(
                icon: Icons.campaign_outlined,
                text: 'MARKETING SOURCE'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: const MarketingSourceSelector(),
            ),

            const SizedBox(height: 36),

            // ── Save button ───────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: GestureDetector(
                onTap: () {
                  final newPatient = PatientModel(
                    id: widget.patient?.id ?? '', // Preserve ID
                    name: _nameCtrl.text.trim(),
                    email: _emailCtrl.text.trim(),
                    phone: _phoneCtrl.text.trim(),
                    city: _cityCtrl.text.trim(),
                    country: _countryCtrl.text.trim(),
                    gender: context.read<AddPatientCubit>().state.gender,
                    dob: _dobCtrl.text.trim(),
                    bloodType: _bloodTypeCtrl.text.trim(),
                    allergies: _allergiesCtrl.text.trim(),
                    skinType: context.read<AddPatientCubit>().state.skinType,
                    contraindications: _contrCtrl.text.trim(),
                    marketingSource:
                        context.read<AddPatientCubit>().state.marketingSource,
                    image: widget.patient?.image ?? '', // Will update with proper logic if available
                    isNew: widget.patient?.isNew ?? true,
                    createdAt: widget.patient?.createdAt ?? DateTime.now(),
                  );
                  context.read<AddPatientCubit>().savePatient(newPatient, isEdit: widget.isedit);
                },
                child: Container(
                  width: double.infinity,
                  height: 52,
                  decoration: BoxDecoration(
                    color: ColorResources.primaryColor,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Center(
                    child: Text(
                      widget.isedit ? 'UPDATE PATIENT' : 'ADD PATIENT',
                      style: const TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: Colors.black,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 3.0,
                      ),
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 12),

            Center(
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(
                  'CANCEL & DISCARD',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor.withOpacity(0.35),
                    fontSize: 11,
                    letterSpacing: 2.0,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

