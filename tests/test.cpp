#include <cstddef>
namespace  NS1
{
struct S {
    void f(int i, float);
    void g(double d) const;
    void h(double d) volatile; // cannot detect volatile...
    constexpr auto i(double d = 12.5) { return 42 * d;}

    virtual int pure() = 0;
    virtual int v();

    template <typename T, std::size_t N> void t(T element, unsigned u, double const& d);

    S() noexcept = default;
    void wi() noexcept(true);
    void wi2() noexcept(false);

    explicit S(double);
};

struct S0 {
    S0() = delete;
    virtual int v();
    virtual int pure();
};

struct S2 : S0 {
    int v() override;
    int pure() final;
    class C {
        C() = default;
    };
};

struct S3 : S2, private S2::C
{};

template <typename T, int N> struct array {
    void f() {
        int i;
    }
    T tab[N];
};
}

