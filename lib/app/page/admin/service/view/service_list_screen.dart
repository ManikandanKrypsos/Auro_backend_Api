import 'package:aura/app/widgets/app_search_bar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';
import '../../../../routes/names.dart';
import '../../../../theme/color/color.dart';
import '../../../../widgets/add_button.dart';
import '../../../../widgets/app_tab_bar.dart';
import '../../../../widgets/custom_appbar.dart';
import '../../../../widgets/secondary_button.dart';
import '../cubit/service_cubit.dart';

// ── Screen ─────────────────────────────────────────────────
class ServiceListScreen extends StatelessWidget {
  const ServiceListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => ServiceCubit(),
      child: const _ServiceListBody(),
    );
  }
}

// ── Body ───────────────────────────────────────────────────
class _ServiceListBody extends StatelessWidget {
  const _ServiceListBody();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: const CustomAppBar(title: 'AURA SERVICES'),
      floatingActionButton: AddButton(onTap: () {
        Get.toNamed(PageRoutes.serviceManageScreen);
      }),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Search — wired to cubit
          AppSearchBar(
            hintText: 'Search services...',
            onChanged: (v) => context.read<ServiceCubit>().search(v),
          ),

          const SizedBox(height: 20),

          // Tab bar
          const _ServiceTabBar(),

          const SizedBox(height: 4),

          // List
          const Expanded(child: _ServiceList()),
        ],
      ),
    );
  }
}

// ── Tab Bar ────────────────────────────────────────────────
class _ServiceTabBar extends StatelessWidget {
  const _ServiceTabBar();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ServiceCubit, ServiceState>(
      buildWhen: (prev, curr) => prev.selectedTab != curr.selectedTab,
      builder: (context, state) {
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            children: [
              Expanded(
                child: AppTab(
                  label: 'FACE',
                  index: 0,
                  selectedTab: state.selectedTab,
                  onTap: (i) => context.read<ServiceCubit>().selectTab(i),
                  activeUnderlineWidth: 100,
                ),
              ),
              Expanded(
                child: AppTab(
                  label: 'BODY',
                  index: 1,
                  selectedTab: state.selectedTab,
                  onTap: (i) => context.read<ServiceCubit>().selectTab(i),
                  activeUnderlineWidth: 100,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ── Service List ───────────────────────────────────────────
class _ServiceList extends StatelessWidget {
  const _ServiceList();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ServiceCubit, ServiceState>(
      buildWhen: (prev, curr) =>
          prev.filteredServices != curr.filteredServices,
      builder: (context, state) {
        if (state.filteredServices.isEmpty) {
          return Center(
            child: Text(
              'NO SERVICES FOUND',
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
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 120),
          itemCount: state.filteredServices.length,
          separatorBuilder: (_, __) => const SizedBox(height: 20),
          itemBuilder: (_, i) =>
              _ServiceCard(service: state.filteredServices[i]),
        );
      },
    );
  }
}

// ── Service Card ───────────────────────────────────────────
class _ServiceCard extends StatelessWidget {
  final Map<String, dynamic> service;
  const _ServiceCard({required this.service});




  @override
  Widget build(BuildContext context) {
    final name = service['name'] as String;
    final price =
        (service['price'] as double).toStringAsFixed(0);
    final duration = service['duration'] as int;
    final description = service['description'] as String;
    final image = service['image'] as String;

    return GestureDetector(
      onTap: () => Get.toNamed(PageRoutes.serviceDetailScreen),
      child: Container(
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(14),
          border:
              Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Image + status badge ──────────────────────
            ClipRRect(
              borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(14)),
              child: Image.network(
                image,
                height: 180,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => _placeholder(),
              ),
            ),
      
            // ── Name + Price ──────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      name,
                      style: const TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 22,
                        fontWeight: FontWeight.w300,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '\$$price',
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 22,
                      fontWeight: FontWeight.w300,
                    ),
                  ),
                ],
              ),
            ),
      
            // ── Duration + Description ────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 6, 16, 0),
              child: Text(
                '$duration min  ·  $description',
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor.withOpacity(0.55),
                  fontSize: 13,
                  fontWeight: FontWeight.w300,
                  height: 1.4,
                ),
              ),
            ),
      
            // ── Action row ────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
              child: Row(
                children: [
                  Expanded(
                    child: SecondaryButton(
        title: "EDIT SERVICE",
        icon: Icons.edit_outlined,
        onTap: () {
      Get.toNamed(PageRoutes.serviceManageScreen);
        },
      )
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _placeholder() => Container(
        height: 180,
        width: double.infinity,
        color: const Color(0xFF1A1A1A),
        child: Icon(Icons.image_outlined,
            color: ColorResources.primaryColor.withOpacity(0.3),
            size: 40),
      );
}