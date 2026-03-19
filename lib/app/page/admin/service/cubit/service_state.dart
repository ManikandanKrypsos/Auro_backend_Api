part of 'service_cubit.dart';


class ServiceState {
  final List<Map<String, dynamic>> allServices;
  final List<Map<String, dynamic>> filteredServices;
  final int selectedTab;
  final String searchQuery;

  const ServiceState({
    required this.allServices,
    required this.filteredServices,
    required this.selectedTab,
    required this.searchQuery,
  });

  ServiceState copyWith({
    List<Map<String, dynamic>>? allServices,
    List<Map<String, dynamic>>? filteredServices,
    int? selectedTab,
    String? searchQuery,
  }) {
    return ServiceState(
      allServices: allServices ?? this.allServices,
      filteredServices: filteredServices ?? this.filteredServices,
      selectedTab: selectedTab ?? this.selectedTab,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}
