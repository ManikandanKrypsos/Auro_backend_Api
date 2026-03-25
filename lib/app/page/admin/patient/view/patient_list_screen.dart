import 'package:aura/app/routes/names.dart';
import 'package:aura/app/widgets/add_button.dart';
import 'package:aura/app/widgets/app_search_bar.dart';
import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';
import '../../../../theme/color/color.dart';
import '../../../../widgets/app_tab_bar.dart';
import '../cubit/patient_cubit.dart';
import '../model/patient_model.dart';

class PatientsScreen extends StatelessWidget {
  const PatientsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => PatientCubit(),
      child: const _PatientsScreenBody(),
    );
  }
}

// ── BODY ───────────────────────────────────────────────────
class _PatientsScreenBody extends StatelessWidget {
  const _PatientsScreenBody();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(title: 'PATIENT DIRECTORY'),
      backgroundColor: ColorResources.blackColor,
      floatingActionButton: AddButton(onTap: ()=>Get.toNamed(PageRoutes.addPatientScreen)),
      body: SafeArea(
        child: Column(
          children: [
            // Search Bar
            AppSearchBar(
              hintText: 'Search patients...',
              onChanged: (v) => context.read<PatientCubit>().search(v),
            ),

            const SizedBox(height: 24),

            // Tabs
            const _PatientTabBar(),

            const SizedBox(height: 16),

            // List
            const Expanded(child: _PatientList()),
          ],
        ),
      ),
    );
  }
}

// ── TAB BAR ────────────────────────────────────────────────
class _PatientTabBar extends StatelessWidget {
  const _PatientTabBar();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<PatientCubit, PatientState>(
      buildWhen: (prev, curr) => prev.selectedTab != curr.selectedTab,
      builder: (context, state) {
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            children: [
              Expanded(
                child: AppTab(
                  label: 'ALL',
                  index: 0,
                  selectedTab: state.selectedTab,
                  onTap: (i) => context.read<PatientCubit>().selectTab(i),
                ),
              ),
              Expanded(
                child: AppTab(
                  label: 'NEW',
                  index: 1,
                  selectedTab: state.selectedTab,
                  onTap: (i) => context.read<PatientCubit>().selectTab(i),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _PatientList extends StatelessWidget {
  const _PatientList();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<PatientCubit, PatientState>(
      buildWhen: (prev, curr) =>
          prev.filteredPatients != curr.filteredPatients ||
          prev.status != curr.status,
      builder: (context, state) {
        if (state.status == PatientStatus.loading) {
          return const Center(
            child: CircularProgressIndicator(
              color: ColorResources.primaryColor,
            ),
          );
        }

        if (state.status == PatientStatus.error) {
          return Center(
            child: Text(
              'Error: ${state.errorMessage}',
              style: const TextStyle(color: Colors.red),
            ),
          );
        }

        if (state.filteredPatients.isEmpty) {
          return Center(
            child: Text(
              'NO PATIENTS FOUND',
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor,
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 3.0,
              ),
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          itemCount: state.filteredPatients.length,
          separatorBuilder: (_, __) => Divider(
            color: ColorResources.whiteColor.withOpacity(0.08),
            thickness: 0.5,
            height: 1,
          ),
          itemBuilder: (context, index) =>
              _PatientCard(patient: state.filteredPatients[index]),
        );
      },
    );
  }
}

// ── PATIENT CARD ───────────────────────────────────────────
// ── PATIENT CARD ───────────────────────────────────────────
class _PatientCard extends StatelessWidget {
  final PatientModel patient;
  const _PatientCard({required this.patient});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Get.toNamed(PageRoutes.patientDetailScreen, arguments: patient),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 20),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // Avatar
            Container(
              width: 72,
              height: 86,
              decoration: BoxDecoration(
                color: ColorResources.cardColor,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(
                  color: ColorResources.borderColor,
                  width: 0.5,
                ),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: Image.network(
                  patient.image,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const Icon(
                    Icons.person,
                    color: ColorResources.borderColor,
                    size: 32,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 14),

            // Info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    patient.name,
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 17,
                      fontWeight: FontWeight.w400,
                      fontStyle: FontStyle.italic,
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    patient.id,
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.0,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Icon(Icons.phone_outlined,
                          color: ColorResources.liteTextColor, size: 12),
                      const SizedBox(width: 5),
                      Text(
                        patient.phone,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor,
                          fontSize: 12,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Action buttons
            GestureDetector(
              onTap: () => Get.toNamed(
                PageRoutes.addPatientScreen,
                arguments: patient,
              ),
              child: const Icon(
                Icons.edit_outlined,
                color: ColorResources.primaryColor,
                size: 15,
              ),
            ),
          ],
        ),
      ),
    );
  }
}