import 'package:bloc/bloc.dart';

part 'service_state.dart';


class ServiceCubit extends Cubit<ServiceState> {
  ServiceCubit()
      : super(ServiceState(
          allServices: _initialServices,
          // Default: tab 0 = face, empty search
          filteredServices: _initialServices
              .where((s) => s['category'] == 'face')
              .toList(),
          selectedTab: 0,
          searchQuery: '',
        ));

  static const List<Map<String, dynamic>> _initialServices = [
    {
      'name': 'Signature Gold Facial',
      'price': 250.0,
      'duration': 60,
      'description': 'Revitalizing 24k gold leaf therapy for instant luminosity.',
      'category': 'face',
      'image': 'https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=600',
    },
    {
      'name': 'Laser Skin Resurfacing',
      'price': 450.0,
      'duration': 45,
      'description': 'Advanced precision laser treatment for skin texture refinement.',
      'category': 'face',
      'image': 'https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=600',
    },
    {
      'name': 'HydraFacial MD',
      'price': 180.0,
      'duration': 50,
      'description': 'Deep cleanse, exfoliate and hydrate for radiant skin.',
      'category': 'face',
      'status': 'active',
      'image': 'https://images.unsplash.com/photo-1512290923902-8a9f81dc236c?w=600',
    },
    {
      'name': 'Deep Tissue Massage',
      'price': 180.0,
      'duration': 90,
      'description': 'Therapeutic release targeting chronic muscle tension.',
      'category': 'body',
      'image': 'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=600',
    },
    {
      'name': 'Hot Stone Therapy',
      'price': 220.0,
      'duration': 75,
      'description': 'Volcanic basalt stones melt tension and restore balance.',
      'category': 'body',
      'image': 'https://images.unsplash.com/photo-1591343395082-e120087004b4?w=600',
    },
    {
      'name': 'Body Sculpt Wrap',
      'price': 290.0,
      'duration': 80,
      'description': 'Detoxifying mineral wrap for inch-loss and skin firmness.',
      'category': 'body',
      'image': 'https://images.unsplash.com/photo-1519823551278-64ac92734fb1?w=600',
    },
  ];

  // ── Tab 0 = face, Tab 1 = body ────────────────────────
  void selectTab(int index) {
    emit(state.copyWith(
      selectedTab: index,
      filteredServices: _applyFilter(
        category: index == 0 ? 'face' : 'body',
        query: state.searchQuery,
      ),
    ));
  }

  // ── Search within the active category ─────────────────
  void search(String query) {
    emit(state.copyWith(
      searchQuery: query,
      filteredServices: _applyFilter(
        category: state.selectedTab == 0 ? 'face' : 'body',
        query: query,
      ),
    ));
  }

  // ── Filter logic ───────────────────────────────────────
  List<Map<String, dynamic>> _applyFilter({
    required String category,
    required String query,
  }) {
    return state.allServices.where((s) {
      final matchesCategory = s['category'] == category;
      final matchesQuery = query.isEmpty ||
          (s['name'] as String)
              .toLowerCase()
              .contains(query.toLowerCase()) ||
          (s['description'] as String)
              .toLowerCase()
              .contains(query.toLowerCase());
      return matchesCategory && matchesQuery;
    }).toList();
  }
}
