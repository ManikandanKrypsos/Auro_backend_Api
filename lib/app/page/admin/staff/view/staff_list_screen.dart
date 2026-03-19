import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';
import '../../../../routes/names.dart';
import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/add_button.dart';
import '../../../../widgets/app_search_bar.dart';
import '../../../../widgets/app_tab_bar.dart';
import '../../../../widgets/custom_appbar.dart';
import '../cubit/staff_cubit.dart';
import '../domain/model/staff_model.dart';

class AdminStaffListScreen extends StatelessWidget {
  const AdminStaffListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => StaffCubit(),
      child: const _StaffScreenBody(),
    );
  }
}

class _StaffScreenBody extends StatelessWidget {
  const _StaffScreenBody();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      floatingActionButton: AddButton(
        onTap: () => Get.toNamed(PageRoutes.addEditStaffScreen),
      ),
      appBar: CustomAppBar(title: 'STAFF MANAGEMENT'),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Search Bar
            AppSearchBar(
              hintText: 'SEARCH...',
              onChanged: (v) => context.read<StaffCubit>().search(v),
            ),

            const SizedBox(height: 24),

            // Tabs
            const _TabBar(),

            const SizedBox(height: 16),

            // Staff List
            const Expanded(child: _StaffList()),
          ],
        ),
      ),
    );
  }
}

// ── TAB BAR ────────────────────────────────────────────────
class _TabBar extends StatelessWidget {
  const _TabBar();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<StaffCubit, StaffState>(
      buildWhen: (prev, curr) => prev.selectedTab != curr.selectedTab,
      builder: (context, state) {
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            children: [
              Expanded(
                child: AppTab(
                  label: 'THERAPISTS',
                  index: 0,
                  selectedTab: state.selectedTab,
                  onTap: (i) => context.read<StaffCubit>().selectTab(i),
                ),
              ),
              Expanded(
                child: AppTab(
                  label: 'RECEPTIONISTS',
                  index: 1,
                  selectedTab: state.selectedTab,
                  onTap: (i) => context.read<StaffCubit>().selectTab(i),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ── STAFF LIST ─────────────────────────────────────────────
class _StaffList extends StatelessWidget {
  const _StaffList();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<StaffCubit, StaffState>(
      buildWhen: (prev, curr) => prev.filteredStaff != curr.filteredStaff,
      builder: (context, state) {
        if (state.filteredStaff.isEmpty) {
          return Center(
            child: Text(
              'NO STAFF FOUND',
              style: AppTextStyles.headingSmall.copyWith(
                color: ColorResources.liteTextColor,
                letterSpacing: 3.0,
              ),
            ),
          );
        }

        return ListView.separated(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          itemCount: state.filteredStaff.length,
          separatorBuilder: (_, __) => Divider(
            color: ColorResources.whiteColor.withOpacity(0.08),
            thickness: 0.5,
            height: 1,
          ),
          itemBuilder: (context, index) =>
              _StaffCard(staff: state.filteredStaff[index]),
        );
      },
    );
  }
}

// ── STAFF CARD ─────────────────────────────────────────────
class _StaffCard extends StatelessWidget {
  final StaffModel staff;
  const _StaffCard({required this.staff});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Get.toNamed(PageRoutes.staffDetailScreen),
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
                  staff.image,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const Icon(
                    Icons.person,
                    color: ColorResources.borderColor,
                    size: 32,
                  ),
                ),
              ),
            ),

            const SizedBox(width: 16),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Name + Status
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Expanded(
                        child: Text(
                          staff.name,
                          style: const TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: ColorResources.whiteColor,
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 2.5,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),

                      GestureDetector(
                        onTap: () => Get.toNamed(
                          PageRoutes.addEditStaffScreen,
                          arguments: true,
                        ),
                        child: Icon(
                          Icons.edit_outlined,
                          size: 16,
                          color: ColorResources.primaryColor,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 5),

                  Text(
                    staff.role,
                    style: AppTextStyles.headingMedium.copyWith(
                      fontStyle: FontStyle.italic,
                      fontSize: 13,
                      fontWeight: FontWeight.w300,
                    ),
                  ),

                  const SizedBox(height: 10),

                  Row(
                    children: [
                      const Icon(
                        Icons.star,
                        color: ColorResources.primaryColor,
                        size: 12,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${staff.rating} RATING',
                        style: AppTextStyles.headingSmall.copyWith(
                          fontSize: 10,
                          color: ColorResources.liteTextColor,
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Icon(
                        Icons.work_outline,
                        color: ColorResources.primaryColor,
                        size: 12,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        staff.experience,
                        style: AppTextStyles.headingSmall.copyWith(
                          fontSize: 10,
                          color: ColorResources.liteTextColor,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
